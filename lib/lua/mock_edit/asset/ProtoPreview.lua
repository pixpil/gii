module 'mock_edit'

CLASS: ProtoPreview ( CanvasView )
	:MODEL{}

function ProtoPreview:__init( env, renderOnly )
	self.currentProto = false
	self.currentProtoInstance = false
	self.renderOnly = renderOnly or false
end

function ProtoPreview:initInput()
	if self.renderOnly then return end
	return ProtoPreview.__super.initInput( self )
end

function ProtoPreview:initAddons()
	if self.renderOnly then return end
	return ProtoPreview.__super.initAddons( self )
end

function ProtoPreview:initEntityEventListener()
	if self.renderOnly then return end
	return ProtoPreview.__super.initEntityEventListener( self )
end

function ProtoPreview:onInstanceCreated( instance )
end

function ProtoPreview:setTaretProto( path )
	self:clear()
	self.currentProto = path
	if path then
		local instance =  mock.createProtoInstance( path )
		self.currentProtoInstance = instance
		if instance then
			instance:setLoc( 0,0,0 )
			self:addSibling( self.currentProtoInstance )
			self:onInstanceCreated( self.currentProtoInstance )
			instance:forceUpdate()
		end
	end
	MOAINodeMgr.update()
	self:updateCanvas()
end

function ProtoPreview:fitViewport( vw, vh )
	local cam = self:getCameraComponent()
	if not self.currentProtoInstance then
		cam:setLoc( 0,0,0 )
		cam:setZoom( 1 )
	else
		local x0,y0,z0,x1,y1,z1 = self.currentProtoInstance:getFullBounds()
		local cx = ( x0 + x1 )/2
		local cy = ( y0 + y1 )/2
		local cz = ( z0 + z1 )/2
		local w, h, d = x1-x0, y1-y0, z1-z0
		cam:setLoc( cx,cy,cz )
		local rx = w/vw
		local ry = h/vh
		local zoom = 1/math.max( rx, ry, 1 )
		cam:setZoom( math.floor( zoom/0.1 ) * 0.1 )
	end
end

function ProtoPreview:clear()
	if not self.currentProtoInstance then return end
	self.currentProtoInstance:destroyWithChildrenNow()
	self.currentProtoInstance = false
end

function ProtoPreview:renderToImage( w, h, img )
	local cam = self:getCameraComponent()
	local targetTexture = mock.RenderTargetTexture()
	
	targetTexture:init(
		w, h,
		'linear', 
		MOAITexture.GL_RGBA8,
		true, true
	)

	cam:setOutputRenderTarget( targetTexture:getRenderTarget() )

	local renderPass = cam:buildRenderPass()
	MOAINodeMgr.update()
	GIIHelper.draw( renderPass )

	local img = img or MOAIImage.new()
	targetTexture:getMoaiFrameBuffer():grabCurrentFrame( img )
	return img
end

--------------------------------------------------------------------
CLASS: ProtoPreviewFactory ()
function ProtoPreviewFactory:__init()
	self.priority = 0
end

function ProtoPreviewFactory:createProtoPreview( env, renderOnly )
	local view = ProtoPreview( env, renderOnly )
	return view
end

--------------------------------------------------------------------

local ProtoPreviewFactories = {}
function registerProtoPreviewFactory( key, factory, priority )
	ProtoPreviewFactories[key] = factory
end

local function _prioritySortFunc( a, b )	
	local pa = a.priority or 0
	local pb = b.priority or 0
	return pa < pb
end


function createProtoPreview( env, renderOnly )
	local factoryList = {}
	for k, f in pairs( ProtoPreviewFactories ) do
		table.insert( factoryList, f )
	end
	table.sort( factoryList, _prioritySortFunc )

	for i, factory in pairs( factoryList ) do
		local view = factory:createProtoPreview( env, renderOnly )
		if view then
			view:setName( 'PROTO_PREVIEW')
			return view
		end
	end
	
	--fallback
	return ProtoPreview( env, renderOnly )
end


local nullFunction = function() end

--------------------------------------------------------------------
function buildProtoThumbnail( protoPath, outputPath, w, h )
	local scn = EditorCanvasScene( _M, { ['use_game_layer'] = true } )
	scn.FLAG_PREVIEW_SCENE = true
	scn:init()

	local dummyRenderContext = GIIMockDummyCanvasContext()

	local nullCanvasEnv = {
		updateCanvas     = nullFunction,
		hideCursor       = nullFunction,
		showCursor       = nullFunction,
		setCursor        = nullFunction,
		setCursorPos     = nullFunction,
		getCanvasSize    = nullFunction,
		startUpdateTimer = nullFunction,
		stopUpdateTimer  = nullFunction,
		contextName      = nullFunction,
		getRenderContext = function() return dummyRenderContext end,
		getMainRenderContext = function() return dummyRenderContext end,
	}

	local preview = createProtoPreview( nullCanvasEnv, true )
	scn:addEntity( preview )

	preview:setTaretProto( protoPath )
	preview:fitViewport( w, h )
	img = preview:renderToImage( w, h )
	img:writePNG( outputPath )

	scn:destroy()
	_collectgarbage( 'collect' )
	return true
end

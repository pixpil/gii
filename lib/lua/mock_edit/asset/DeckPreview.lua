module 'mock_edit'

CLASS: DeckPreview ( CanvasView )
	:MODEL{}

function DeckPreview:__init( env, renderOnly )
	self.currentDeck = false
	self.renderOnly = renderOnly or false

	self.deckEntity = false
	self.deckComponent = false	
end

function DeckPreview:initInput()
	if self.renderOnly then return end
	return DeckPreview.__super.initInput( self )
end

function DeckPreview:initAddons()
	if self.renderOnly then return end
	return DeckPreview.__super.initAddons( self )
end

function DeckPreview:initEntityEventListener()
	if self.renderOnly then return end
	return DeckPreview.__super.initEntityEventListener( self )
end

function DeckPreview:onInit()
	self.deckEntity = mock.Entity()
	self.deckComponent = self.deckEntity:attach( mock.DeckComponent() )
	self:addSibling( self.deckEntity )
	setPropBlend( self.deckComponent:getMoaiProp(), 'alpha' )
end

function DeckPreview:setTargetDeck( path )
	self.currentDeck = path
	if path then
		self.deckComponent:setDeck( path )
	else
		self.deckComponent:setDeck( false )
	end
	MOAINodeMgr.update()
	self:updateCanvas()
end

function DeckPreview:fitViewport( vw, vh )
	local cam = self:getCameraComponent()
	if not self.currentDeck then
		cam:setLoc( 0,0,0 )
		cam:setZoom( 1 )
	else
		local x0,y0,z0,x1,y1,z1 = self.deckEntity:getFullBounds()
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

function DeckPreview:clear()
	self.currentDeck = false
	self.deckComponent:setDeck( false )
end

function DeckPreview:renderToImage( w, h, img )
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
CLASS: DeckPreviewFactory ()
function DeckPreviewFactory:__init()
	self.priority = 0
end

function DeckPreviewFactory:createDeckPreview( env, renderOnly )
	local view = DeckPreview( env, renderOnly )
	return view
end

--------------------------------------------------------------------

local DeckPreviewFactories = {}
function registerDeckPreviewFactory( key, factory, priority )
	DeckPreviewFactories[key] = factory
end

function createDeckPreview( env, renderOnly )
	local factoryList = {}
	for k, f in pairs( DeckPreviewFactories ) do
		table.insert( factoryList, f )
	end
	-- table.sort( factoryList, prioritySortFunc )

	for i, factory in pairs( factoryList ) do
		local view = factory:createDeckPreview( env, renderOnly )
		if view then
			view:setName( 'DECK_PREVIEW')
			return view
		end
	end
	
	--fallback
	return DeckPreview( env, renderOnly )
end


local nullFunction = function() end

--------------------------------------------------------------------
function buildDeckThumbnail( deckPath, outputPath, w, h )
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
	}

	local preview = createDeckPreview( nullCanvasEnv, true )
	scn:addEntity( preview )

	preview:setTargetDeck( deckPath )
	preview:fitViewport( w, h )
	img = preview:renderToImage( w, h )
	img:writePNG( outputPath )

	scn:clear()
	return true
end

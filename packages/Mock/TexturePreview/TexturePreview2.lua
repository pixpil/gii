--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

CLASS: Preview ( mock_edit.EditorEntity )
function Preview:onLoad()
	local prop = MOCKProp.new()
	self.prop = prop
	self.zoom = 1
	self.dragging = false
	mock.installInputListener( self, { device = scn:getEditorInputDevice() } )
	self:_attachProp( prop )
end

function Preview:onDestroy()
	uninstallInputListener( self )
end

function Preview:onMouseDown()
	updateCanvas()
end

function Preview:show( path )
	local texture = mock.loadAsset(path)
	if not texture then return false end 
	if texture:isInstance( 'RenderTargetTexture' ) and ( not texture.updated ) then return false end

	-- self.navigate:reset()
	self.zoom = 1

	local deck = MOAISpriteDeck2D.new()
	local w, h = texture:getOutputSize()
	deck:setRect( -w/2, -h/2, w/2, h/2 )
	deck:setTexture( texture:getMoaiTexture() )
	deck:setUVRect( texture:getUVRect() )
	self.prop:setDeck( deck )
	self.prop:forceUpdate()
	setPropBlend( self.prop, 'alpha' )
	updateCanvas()
end

function Preview:fitViewport()
end

preview = scn:addEntity( Preview() )


function show( path )
	preview:show( path )
end


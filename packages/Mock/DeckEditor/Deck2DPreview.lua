--------------------------------------------------------------------
-- scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

scn = mock_edit.EditorCanvasScene( _M, { ['use_game_layer'] = true } )
scn.FLAG_PREVIEW_SCENE = true
scn:init()

preview = mock_edit.createDeckPreview( _M )
scn:addEntity( preview )


-- --------------------------------------------------------------------
-- scn = mock_edit.createSimpleEditorCanvasScene( _M )
-- --------------------------------------------------------------------

CLASS: Preview ( mock_edit.EditorEntity )
function Preview:onLoad()
	local prop = MOAIGraphicsProp.new()
	local gridProp = MOAIGraphicsGridProp.new()
	self.prop = prop
	self.gridProp = gridProp
	self.zoom = 1
	self:_attachProp( prop )
	self:_attachProp( gridProp )
	setPropBlend( prop, 'alpha' )
	setPropBlend( gridProp, 'alpha' )
end

function Preview:show( path )
	local deck = mock.loadAsset(path)
	deck = deck and deck:getMoaiDeck()
	if not deck then return false end 
	if deck:getClass() == MOAITileDeck2D then
		local grid = MOAIGrid.new()
		local mockDeck = deck.source
		local col, row = mockDeck.col, mockDeck.row
		local tw , th  = mockDeck.tw, mockDeck.th
		local sp = mockDeck.spacing
		grid:setSize( col, row, tw + sp, th + sp, 0, 0, tw, th)
		local t = 1
		for j = row, 1, -1 do
			for i = 1, col do
				grid:setTile( i, j, t )
				t=t+1
			end
		end
		self.gridProp:setGrid( grid )
		self.gridProp:setDeck( deck )
		self.gridProp:forceUpdate()
		self.gridProp:setVisible( true )
		self.prop:setVisible( false )
	else
		self.prop:setDeck( deck )
		self.prop:forceUpdate()
		self.prop:setVisible( true )
		self.gridProp:setVisible( false )
	end
	
	updateCanvas()
end


preview = scn:addEntity( Preview() )

function show( path )
	preview:show( path )
end

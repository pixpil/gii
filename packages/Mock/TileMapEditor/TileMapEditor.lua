--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

mock_edit.addColor( 'tilemap_grid', hexcolor( '#007fff', 0.3 ) )


--------------------------------------------------------------------
CLASS: NamedTilesetLayout ( mock_edit.EditorEntity )
	:MODEL{}

function NamedTilesetLayout:onLoad()
	self.tileProps = {}
	self.target = false
	self.selectedTile = false
	self.selectedTileId = false

end

function NamedTilesetLayout:setTarget( tileset )
	self.target = tileset
	
	local count = tileset:getTileCount()
	local deck  = tileset:getMoaiDeck()

	local bx0 = 1000000
	local by0 = 1000000
	local bx1 = -1000000
	local by1 = -1000000
	for id = 1, count do
		local name = tileset.idToName[ id ]
		local data = tileset.nameToTile[ name ]
		local x0,y0,x1,y1 = unpack( data['raw_rect'])
		local ox,oy = unpack( data['deck_offset'])
		local index = data['raw_index']
		local prop = MOAIGraphicsProp.new()
		self:_attachProp( prop )
		local prop2 = MOAIGraphicsProp.new()
		self:_attachProp( prop2 )
		
		local x, y = x0 - ox, -y1 - oy
		bx0 = math.min( x, bx0 )
		bx1 = math.max( x, bx1 )
		by0 = math.min( y, by0 )
		by1 = math.max( y, by1 )

		prop:setLoc( x, y, index*0.01 )
		prop:setColor( 1,1,1, 1 )
		prop:setDeck( deck )
		prop:setBounds( ox, oy, 0, x1 - x0 + ox, y1 - y0 +oy, 0 )
		-- prop:setBounds( x0 -x, y0 - y, 0, x1 - x, y1 - y, 0 )
		-- print( name,x0 -x, y0 - y, 0, x1 - x, y1 - y, 0 )
		prop:setIndex( id )
		prop2:setLoc( x, y, index*0.01 + 0.1 )
		prop2:setColor( 0.5,0.5,1, 1 )
		-- prop2:setDeck( deck )
		local xx0,yy0,zz0, xx1,yy1,zz1 = prop:getBounds()
		local boundDeck = MOAIDrawDeck.new()
		boundDeck:setDrawCallback(function()
			MOAIDraw.setPenColor( 0.7,0.2,.7, 0.2 )
			MOAIDraw.fillRect( xx0,yy0, xx1,yy1  )
			MOAIDraw.setPenColor( 0.5,0.5,1, 1 )
			MOAIDraw.drawRect( xx0,yy0, xx1,yy1  )
		end)
		prop2:setDeck( boundDeck )
		prop2:setBounds( prop:getBounds() )
		prop2.deck = boundDeck
		prop2:setIndex( id )
		prop2:setVisible( false )
		setPropBlend( prop, 'alpha' )
		setPropBlend( prop2, 'alpha' )
		prop.selectionProp = prop2

		self.tileProps[ id ] = prop
	end
	self:setLoc( -(bx0+bx1)/2, -(by0+by1)/2 )
end

function NamedTilesetLayout:selectTile( name )
	if self.selectedTileId then
		local prevProp = self.tileProps[ self.selectedTileId ]
		-- prevProp:setColor( 1,1,1, 1 )
		prevProp.selectionProp:setVisible( false )
	end

	if name then
		local id = self.target.nameToId[ name ]
		local prop = self.tileProps[ id ]
		self.selectedTile = name
		self.selectedTileId = id
		-- prop:setColor( 1, .7, .7, 1 )
		prop.selectionProp:setVisible( true )
	else
		self.selectedTile = false
		self.selectedTileId = false
	end
end

function NamedTilesetLayout:pickTile( x, y )
	if not self.target then return nil end
	local found = false
	for i, prop in pairs( self.tileProps ) do
		local _,_,z1 = prop:getWorldLoc()
		if prop:inside( x, y, z1 ) then
			found = i
			break
		end
	end
	return self.target.idToName[ found ], found
end

function NamedTilesetLayout:onDestroy()
	for i, p in ipairs( self.tileProps ) do
		self:_detachProp( p.selectionProp )
		self:_detachProp( p )
	end
end

--------------------------------------------------------------------
CLASS: TilesetViewer ( mock_edit.EditorEntity )
	:MODEL{}

function TilesetViewer:__init()
	self.targetTilesetPath = false
	self.targetTileset = false
	self.currentLayout = false
	self.selectedTile = false
end

function TilesetViewer:onLoad()
	-- self.navigate = self:addChild( mock_edit.CanvasNavigate() )
	local inputDevice = self:getScene():getEditorInputDevice()
	self:attach( mock.InputScript{ 
			device = inputDevice
		} )
end

function TilesetViewer:onMouseDown( btn, x,y )
	if btn ~= 'left' then return end
	if not self.currentLayout then return end
	local wx, wy = self:wndToWorld( x, y )
	local name = self.currentLayout:pickTile( wx, wy )
	if name then
		self.currentLayout:selectTile( name )
	end
	if mock_edit.getCurrentSceneView():getActiveToolId() ~= 'tilemap.fill' then
		self.parentEditor:changeTool( 'pen' )
		mock_edit.getCurrentSceneView():changeSceneTool( 'tilemap_pen' )
	end
	self.parentEditor:selectTileBrush( name )
	updateCanvas()
end

function TilesetViewer:setTargetTileset( tilesetPath )
	if self.targetTilesetPath == tilesetPath then return end
	self.targetTilesetPath = tilesetPath
	self.targetTileset = tilesetPath and mock.loadAsset( tilesetPath )

	self.parentEditor:selectTileBrush( false )
	if self.currentLayout then
		self.currentLayout:destroyAllNow()
		self.currentLayout = false
	end
	if not self.targetTileset then return self:hide() end
	self:show()

	--build tile layout
	if self.targetTileset:isInstance( mock.NamedTileset ) then
		self.currentLayout = self:addChild( NamedTilesetLayout() )
		self.currentLayout:setTarget( self.targetTileset )
	else
		--TODO
	end
end

function TilesetViewer:fitViewport( w, h )
end

function TilesetViewer:clearSelection()
	if self.currentLayout then self.currentLayout:selectTile( false ) end
	self.parentEditor:selectTileBrush( false )
	updateCanvas()
end

--------------------------------------------------------------------
local colors = {
	{hexcolor"#725800"},
	{hexcolor"#405805"},
	{hexcolor"#822e25"},
}

local randcolors =  {}
local function getRandomColor( id )
	local c = randcolors [ id ]
	if c then return c end
	c = { rand(0,1), rand(0,1), rand(0,1), 1 }
	randcolors[ id ] = c
	return c
end

local markTileWidth, markTileHeight = 1, 1
local markTileDeck
if not MOAIGeometry2DDeck then
	markTileDeck = MOAIDrawDeck.new()
	markTileDeck:setDrawCallback( function( idx, x, y, xScl, yScl )
		-- MOAIDraw.setPenColor( unpack( getRandomColor( idx ) ) )
		MOAIDraw.setPenColor( hexcolor( '#52a1ff', 0.7 ) )
		-- x = x - tileSize/2
		-- y = y - tileSize/2
		-- MOAIDraw.fillRect( x, y, x+tileSize-1, y+tileSize-1 )
		local w = xScl * markTileWidth - 2
		local h = yScl * markTileHeight - 2
		MOAIDraw.drawRect( 
			x,
			y,
			x + w,
			y + h
		)
		-- MOAIDraw.drawRect( 
		-- 	x - w/2 + 1,
		-- 	y - h/2 + 1,
		-- 	x + w/2,
		-- 	y + h/2
		-- )
	end
	)
else
	markTileDeck = MOAIGeometry2DDeck.new()
	markTileDeck:reserve( 1 )
end

local function updateMarkTileDeck()
	if not MOAIGeometry2DDeck then
		return
	else
		markTileDeck:setRectItem( 
			1, 
			markTileWidth*0.05, markTileHeight*0.05, markTileWidth*0.95, markTileHeight*0.95, 
			hexcolor( '#52a1ff', 0.7 )
		)
	end
end

--------------------------------------------------------------------
CLASS: TileMapGridLines ( mock_edit.EditorEntity )
	:MODEL{}

function TileMapGridLines:__init()
	self.targetLayer = false
	assert( self.FLAG_EDITOR_OBJECT )
end

function TileMapGridLines:onLoad()
	self:attach( mock.DrawScript() ):setBlend( 'alpha' )
	self.markProp = MOAIGraphicsGridProp.new()	
	self.markProp:setDeck( markTileDeck )
	setPropBlend( self.markProp, 'alpha' )
end

function TileMapGridLines:onDraw()
	if not self.targetLayer then return end
	mock_edit.applyColor( 'tilemap_grid' )
	self.targetLayer:onDrawGridLine()
end

function TileMapGridLines:onDestroy()
	self:_detachProp( self.markProp )
	if self.debugDrawProp then
		self:_detachProp( self.debugDrawProp )
	end
end

function TileMapGridLines:setTarget( targetLayer )
	self.targetLayer = targetLayer
	self.markProp:setGrid( targetLayer:getMoaiGrid() )
	local debugDrawProp = targetLayer:getDebugDrawProp()
	self.debugDrawProp = debugDrawProp
	if debugDrawProp then
		self:_attachProp( debugDrawProp )
	else
		self:_attachProp( self.markProp )
	end

	local tw, th = targetLayer:getTileSize()
	local cw, ch = targetLayer:getCellSize()
	local w, h = tw/cw, th/ch
	markTileWidth, markTileHeight = w, h
	updateMarkTileDeck()
	markTileDeck:setRect( 0,0, w, h )
	-- print( tw/cw, th/ch )
end

--------------------------------------------------------------------
CLASS: TileBrush ()
	:MODEL{}

function TileBrush:__init()
	self.grid = mock.GridStruct()
	self.tiles = {}
end

function TileBrush:paint( layer, x, y )
end

function TileBrush:paintRandom( layer, x, y )
end


--------------------------------------------------------------------
CLASS: TileMapEditor( mock_edit.EditorEntity )

function TileMapEditor:__init()
	self.currentTerrainBrush = false
	self.currentTileBrush    = false
	self.randomEnabled       = false
	self.tileBrush           = false

	self.targetTileMap = false
	self.targetTileMapLayer = false
	self.viewSelectedOnly = false
end

function TileMapEditor:onLoad()
	self.tilesetViewer = self:addSibling( TilesetViewer() )
	self.tilesetViewer.parentEditor = self
	self.gridLine = false
end

function TileMapEditor:setViewSelectedOnly( toggle )
	self.viewSelectedOnly = toggle
	return self:refreshLayerVisibility()
end

function TileMapEditor:refreshLayerVisibility()
	if not self.targetTileMap then return end
	if self.viewSelectedOnly and self.targetTileMapLayer then
		for i, layer in ipairs( self.targetTileMap:getLayers() ) do
			local selected = self.targetTileMapLayer == layer
			layer:setVisible( selected )
		end
	else
		for i, layer in ipairs( self.targetTileMap:getLayers() ) do
			layer:setVisible( true )
		end
	end
	mock_edit.getCurrentSceneView():updateScene()
end

function TileMapEditor:findTargetTileMap()
	local selection = gii.getSelection( 'scene' )
	--find a parent animator
	if #selection ~= 1 then --only single selection allowed( for now )
		return nil
	end

	local ent = selection[1]
	if not isInstance( ent, mock.Entity ) then
		return nil
	end

	--while ent do
		local map = ent:getComponent( mock.TileMap )
		if map then return map end
		--ent = ent.parent
	--end

	return nil
end

function TileMapEditor:setTargetTileMap( m )
	local prevMap = self.targetTileMap
	self.targetTileMap = m
	if prevMap then
		for i, layer in ipairs( prevMap:getLayers() ) do
			layer:setVisible( true )
		end	
	end
	self:refreshLayerVisibility()
end

function TileMapEditor:setTargetTileMapLayer( l )
	if self.gridLine then
		self.gridLine:destroyAllNow()
		self.gridLine = false
	end

	self.targetTileMapLayer  = l
	self.currentTileBrush    = false
	-- self.currentTileBrush    = 'WallBrick.s'
	self.currentTerrainBrush = false
	if self.targetTileMapLayer then
		self.tilesetViewer:setTargetTileset( self.targetTileMapLayer:getTilesetPath() )
		self.gridLine = self.targetTileMap._entity:addChild( TileMapGridLines() )
		self.gridLine:setTarget( self.targetTileMapLayer )
	else
		self.tilesetViewer:setTargetTileset( false )
	end
	self:refreshLayerVisibility()
end

function TileMapEditor:getTargetTileMapLayer()
	return self.targetTileMapLayer
end

function TileMapEditor:getTargetTileMap()
	return self.targetTileMap
end

function TileMapEditor:wndToCoord( x, y )
	local sceneView = mock_edit.getCurrentSceneView()
	x, y = sceneView:wndToWorld( x, y )
	layer = self.targetTileMapLayer
	local lx, ly = layer:worldToModel( x, y )
	local tx, ty = layer:locToCoord( lx, ly ) 
	return tx, ty
end

function TileMapEditor:requestAvailTileMapLayerTypes()
	if not self.targetTileMap then return {} end
	return self.targetTileMap:getAvailTileMapLayerTypes()
end

function TileMapEditor:createTileMapLayer( tileset )
	if not self.targetTileMap.initialized then
		mock_edit.alertMessage( 'message', 'Tilemap not initialized', 'info' )
		return false
	end

	local layer = self.targetTileMap:_createLayer( tileset )
	if not layer then
		mock_edit.alertMessage( 'message', 'unsupported Tileset type', 'info' )
		return false
	end
	self:getTargetTileMap():markDataModified()
	return layer
end

function TileMapEditor:removeTileMapLayer()
	if not self.targetTileMapLayer then return end
	self.targetTileMap:removeLayer( self.targetTileMapLayer )
	self.targetTileMapLayer = false
	self:getTargetTileMap():markDataModified()
end

function TileMapEditor:moveTileMapLayerUp( layer )
	local map = layer.parentMap
	local order = layer.order
	if order > 1 then
		local upper = map.layers[ order - 1 ]
		if not upper then return end
		upper:setOrder( order )
		layer:setOrder( order - 1 )
	end
	self:getTargetTileMap():markDataModified()
end

function TileMapEditor:moveTileMapLayerDown( layer )
	local map = layer.parentMap
	local order = layer.order
	local count = #map.layers
	if order < count then
		local lower = map.layers[ order + 1 ]
		if not lower then return end
		lower:setOrder( order )
		layer:setOrder( order + 1 )
	end
	self:getTargetTileMap():markDataModified()
end

function TileMapEditor:selectCodeTile( tile )
	local name = tile.name
	self:selectTileBrush( name )
	if mock_edit.getCurrentSceneView():getActiveToolId() ~= 'tilemap.fill' then
		self:changeTool( 'pen' )
	end
end

function TileMapEditor:selectTileBrush( id, additive )
	self.currentTileBrush = id
end

function TileMapEditor:getTileBrush()
	return self.currentTileBrush
end

function TileMapEditor:setTerrainBrush( brush )
	self.currentTerrainBrush = brush
	-- self:changeTool( 'terrain' )
end

function TileMapEditor:getTerrainBrush()
	return self.currentTerrainBrush
end

function TileMapEditor:changeTool( id )
	if not self.targetTileMapLayer then
		mock_edit.alertMessage( 'message', 'no target tilemap layer selected', 'info' )
		return
	end

	if id == 'pen' then		
		mock_edit.getCurrentSceneView():changeCanvasTool( 'tilemap.pen' )
		_module.clearTerrainSelection()

	elseif id == 'eraser' then
		mock_edit.getCurrentSceneView():changeCanvasTool( 'tilemap.eraser' )
		_module.clearTerrainSelection()
		_module.clearCodeTileSelection()
		self.tilesetViewer:clearSelection()

	elseif id == 'flip_x' then
		mock_edit.getCurrentSceneView():changeCanvasTool( 'tilemap.flip_x' )

	elseif id == 'fill' then
		mock_edit.getCurrentSceneView():changeCanvasTool( 'tilemap.fill' )

	elseif id == 'terrain' then
		mock_edit.getCurrentSceneView():changeCanvasTool( 'tilemap.terrain' )
		self.tilesetViewer:clearSelection()
		
	end
end

function TileMapEditor:clearLayer()
	if not self.targetTileMapLayer then
		mock_edit.alertMessage( 'message', 'no target tilemap layer selected', 'info' )
		return
	end
	self:getTargetTileMapLayer():getMoaiGrid():fill(0)
	self:getTargetTileMap():markDataModified()
	mock_edit.getCurrentSceneView():updateScene()
end	

function TileMapEditor:toggleToolRandom( enabled )
	self.randomEnabled = enabled
end

function TileMapEditor:incSubDivision()
	if not self.targetTileMapLayer then return end
	local subD = self.targetTileMapLayer.subdivision + 1
	if subD <= 4 then
		self.targetTileMapLayer:setSubDivision( subD )
		self:getTargetTileMap():markDataModified()
	end
end

function TileMapEditor:decSubDivision()
	if not self.targetTileMapLayer then return end
	local subD = self.targetTileMapLayer.subdivision - 1
	if subD >= 1 then
		self.targetTileMapLayer:setSubDivision( subD )
		self:getTargetTileMap():markDataModified()
	end
end

--------------------------------------------------------------------
CLASS: TileMapToolPen ( mock_edit.CanvasTool )
	:MODEL{}

function TileMapToolPen:__init()
	self.pressed = false
	self.action = false
	self.drawFromPos = { 0, 0 }

end

function TileMapToolPen:updateDrawFromPos( x, y )
	self.drawFromPos = { x, y }
end

function TileMapToolPen:getDrawFromPos()
	return unpack( self.drawFromPos )
end

function TileMapToolPen:onMouseDown( btn, x, y )
	if self.pressed then return end
	if btn == 'left' then 
		self.action = 'normal'
		self:_doAction( x, y )

	elseif btn == 'right' then
		self.action = 'optional'
		self:_doAction( x, y )

	else
		return
	end
	self.pressed = btn
end

local function _drawArea( x0, y0, x1, y1, step, func )
	if x0 > x1 then 
		local t = x0
		x0, x1 = x1, t
	end
	if y0 > y1 then 
		local t = y0
		y0, y1 = y1, t
	end
	for y = y0,y1 do
		for x = x0,x1 do
			func( x, y )
		end
	end
end

local function _drawxLine( x0, y0, x1, y1, step, func )	
	local dx = x1 - x0
	local dy = y1 - y0
	step = step or 1
	if math.abs( dx ) > math.abs( dy ) then
		--loop x axis
		local count = math.floor( math.abs( dx ) / step )
		if count == 0 then return end
		local stepY = dy / count
		local stepX = dx > 0 and step or - step
		for i = 0, count do
			local x = i * stepX + x0
			local y = i * stepY + y0
			func( x, y )
		end
	else
		--loop y axis
		local count = math.floor( math.abs( dy ) / step )
		if count == 0 then return end
		local stepX = dx / count
		local stepY = dy > 0 and step or - step
		for i = 0, count do
			local x = i * stepX + x0
			local y = i * stepY + y0
			func( x, y )
		end
	end
end



function TileMapToolPen:onAction( action, layer, x, y, dragging )
	if action == 'normal' then
		if self:getInputDevice():isShiftDown() and ( not dragging ) then
			--Draw Line
			local brush = editor:getTileBrush()
			if brush then
				local x0, y0 = self:getDrawFromPos()
				_drawArea( x0, y0, x, y, 1, 
					function( tx, ty )
						layer:setTile( tx,ty, brush )
					end
				)
				self:updateDrawFromPos( x, y )
			end
		else
			local brush = editor:getTileBrush()
			if brush then
				layer:setTile( x,y, brush )
				self:updateDrawFromPos( x, y )
			end
		end
	elseif action == 'optional' then
		if self:getInputDevice():isShiftDown() and ( not dragging ) then
			local x0, y0 = self:getDrawFromPos()
			_drawArea( x0, y0, x, y, 1, 
				function( tx, ty )
					layer:setTile( tx,ty, false )
				end
			)
			self:updateDrawFromPos( x, y )
		else
			layer:setTile( x,y, false )
			self:updateDrawFromPos( x, y )
		end
	end
end

function TileMapToolPen:onMouseUp( btn, x, y )
	if self.pressed ~= btn then return end
	self.pressed    = false
	self.targetRoom = false
end

function TileMapToolPen:onMouseMove( x, y )
	if not self.pressed then return end
	self:_doAction( x, y, true )
end

function TileMapToolPen:_doAction( x, y, dragging )
	local layer  = editor:getTargetTileMapLayer()
	if not layer then
		if not dragging then
			mock_edit.alertMessage( 'message', 'no target tile map', 'info' )
		end
		return false
	end
	local tx, ty = editor:wndToCoord( x, y )
	if layer:isValidCoord( tx, ty ) then
		self:onAction( self.action, layer, tx, ty, dragging )
		layer:getMap():markDataModified()
		gii.emitPythonSignal( 'entity.modified', editor.targetTileMap )
	end
end

mock_edit.registerCanvasTool( 'tilemap.pen', TileMapToolPen )


--------------------------------------------------------------------
CLASS: TileMapToolEraser ( TileMapToolPen )

function TileMapToolEraser:onAction( action, layer, x, y, dragging )
	if action == 'normal' then
		if self:getInputDevice():isShiftDown() and ( not dragging ) then
			local x0, y0 = self:getDrawFromPos()
			_drawArea( x0, y0, x, y, 1, 
				function( tx, ty )
					layer:setTile( tx,ty, false )
				end
			)
			self:updateDrawFromPos( x, y )
		else
			layer:setTile( x,y, false )
			self:updateDrawFromPos( x, y )
		end
	else
	end
end

mock_edit.registerCanvasTool( 'tilemap.eraser', TileMapToolEraser )



--------------------------------------------------------------------
-- CLASS: TileMapToolFlipX ( TileMapToolPen )

-- local FLAG_FLIPX = MOAIGrid.TILE_X_FLIP
-- function TileMapToolFlipX:onAction( action, layer, x, y, dragging )
-- 	if self:getInputDevice():isShiftDown() and ( not dragging ) then
-- 		local x0, y0 = self:getDrawFromPos()
-- 		if action == 'normal' then
-- 			_drawArea( x0, y0, x, y, 1, 
-- 				function( tx, ty )
-- 					layer:setTileFlags( tx,ty, FLAG_FLIPX )
-- 				end
-- 			)
-- 		else
-- 			_drawArea( x0, y0, x, y, 1, 
-- 				function( tx, ty )
-- 					layer:clearTileFlags( tx,ty, FLAG_FLIPX )
-- 				end
-- 			)
-- 		end
-- 		self:updateDrawFromPos( x, y )
-- 	else
-- 		if action == 'normal' then
-- 			layer:setTileFlags( x,y, FLAG_FLIPX )
-- 		else
-- 			layer:clearTileFlags( x,y, FLAG_FLIPX )
-- 		end
-- 		self:updateDrawFromPos( x, y )
-- 	end
-- end

-- mock_edit.registerCanvasTool( 'tilemap.flip_x', TileMapToolFlipX )



--------------------------------------------------------------------
CLASS: TileMapToolFill ( TileMapToolPen )

local _floodFill
if MOCKGridHelper then
	_floodFill = function( grid, x, y, w, h, id0, id1 )
		if x < 1 then return end
		if y < 1 then return end
		if x > w then return end
		if y > h then return end
		MOCKGridHelper.floodFill( grid, x, y, id1 )
	end
else
	_floodFill = function( grid, x, y, w, h, id0, id1 )
		if x < 1 then return end
		if y < 1 then return end
		if x > w then return end
		if y > h then return end
		local id = grid:getTile( x, y )
		if id ~= id0 then return end
		grid:setTile( x, y, id1 )
		_floodFill( grid, x+1, y, w, h, id0, id1 )
		_floodFill( grid, x-1, y, w, h, id0, id1 )
		_floodFill( grid, x, y+1, w, h, id0, id1 )
		_floodFill( grid, x, y-1, w, h, id0, id1 )
	end
end

function TileMapToolFill:onAction( action, layer, x, y, dragging )
	local brush = editor:getTileBrush()
	--flood fill
	if not brush then return end
	local layer = editor:getTargetTileMapLayer()
	local grid = layer:getMoaiGrid()
	local brushId = layer:tileIdToGridId( brush )
	local id0 = grid:getTile( x, y )
	local w, h = grid:getSize()
	if action == 'normal' then
		if id0 == brushId then return end
		_floodFill( grid, x,y, w,h, id0, brushId )
	elseif action == 'optional' then
		_floodFill( grid, x,y, w,h, id0, 0 )

	end
end

mock_edit.registerCanvasTool( 'tilemap.fill', TileMapToolFill )


--------------------------------------------------------------------
CLASS: TileMapToolTerrain ( TileMapToolPen )

function TileMapToolTerrain:onAction( action, layer, x, y, dragging )
	local ignoreTerrainKind = false
	if self:getInputDevice():isCtrlDown() then
		ignoreTerrainKind = true
	end
	if self:getInputDevice():isShiftDown() and ( not dragging ) then
		local x0, y0 = self:getDrawFromPos()
		if action == 'normal' then
			_drawArea( x0, y0, x, y, 1, 
				function( tx, ty )
					self:paint( layer, tx, ty, ignoreTerrainKind )
				end
			)
		else
			_drawArea( x0, y0, x, y, 1, 
				function( tx, ty )
					self:remove( layer, tx, ty, ignoreTerrainKind )
				end
			)
		end
	else
		if action == 'normal' then
			self:paint( layer, x, y, ignoreTerrainKind )
		else
			self:remove( layer, x, y, ignoreTerrainKind )
		end
	end
	self:updateDrawFromPos( x, y )
end

function TileMapToolTerrain:paint( layer, x, y, ignoreTerrainKind )
	local brush = editor:getTerrainBrush()
	if not brush then return end
	
	local brushSize = 1
	local terrain1 = brush:getTerrainId()
	local tileset = editor:getTargetTileMapLayer():getTileset()

	local x0, x1 =  x + math.ceil(-brushSize/2), x + math.floor(brushSize/2)
	local y0, y1 =  y + math.ceil(-brushSize/2), y + math.floor(brushSize/2)

	if not ignoreTerrainKind then
		for yy = y0 - 1, y1 + 1 do
		for xx = x0 - 1, x1 + 1 do
			-- if xx < x0 or xx > x1 or yy < y0 or yy > y1 then
				local terrain0 = layer:getTerrain( xx, yy )
				if terrain0 and terrain0 ~= terrain1 then
					local brush0 = tileset:getTerrainBrush( terrain0 )
					if brush0 then
						brush0:remove( layer, xx, yy )
					end
				end
			-- end
		end
		end
	end

	for yy = y0, y1 do
	for xx = x0, x1 do
		brush:paint( layer, xx, yy, ignoreTerrainKind )
	end
	end
end

function TileMapToolTerrain:remove( layer, x, y, ignoreTerrainKind )
	local brushSize = 1
	local tileset = editor:getTargetTileMapLayer():getTileset()

	local x0, x1 =  x + math.ceil( -brushSize / 2 ), x + math.floor( brushSize / 2 )
	local y0, y1 =  y + math.ceil( -brushSize / 2 ), y + math.floor( brushSize / 2 )
	for yy = y0, y1 do
	for xx = x0, x1 do
		local terrain0 = layer:getTerrain( xx, yy )
		local brush0 = tileset:getTerrainBrush( terrain0 )
		if brush0 then
			brush0:remove( layer, xx, yy )
		end
	end
	end
end

mock_edit.registerCanvasTool( 'tilemap.terrain', TileMapToolTerrain )


--------------------------------------------------------------------
editor = scn:addEntity( TileMapEditor() )



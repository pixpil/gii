markProtoInstanceOverrided = mock.markProtoInstanceOverrided
--------------------------------------------------------------------
CLASS: DeckCanvasBrush ()
	:MODEL{}

function DeckCanvasBrush:__init()
end

function DeckCanvasBrush:paint( canvas, x, y, z, dragging )
end


--------------------------------------------------------------------
CLASS: DeckCanvasSingleDeckBrush ( DeckCanvasBrush )
	:MODEL{}

function DeckCanvasSingleDeckBrush:__init()
	self.deck = false
	self.intialScl  = false
end

function DeckCanvasSingleDeckBrush:paint( canvas, x, y, z, dragging )
	if dragging then return end
	local prop = canvas:addProp( self.deck )
	if prop then
		prop:setLoc( x, y, z )
		if self.intialScl then
			prop:setScl( unpack( self.intialScl ) )
		end
	end
	return prop
end

function DeckCanvasSingleDeckBrush:setInitialScl( intialScl )
	self.intialScl = intialScl
end

function DeckCanvasSingleDeckBrush:setDecks( decks )
	self.decks = decks
	self.deck = decks[1] or false
end

--------------------------------------------------------------------
CLASS: DeckCanvasEraseBrush ( DeckCanvasBrush )
	:MODEL{}

function DeckCanvasEraseBrush:__init()
	self.dragDistance = 0
	self.x0 = 0
	self.y0 = 0
end

function DeckCanvasEraseBrush:paint( canvas, x, y, z, dragging )
	if dragging then
		self.dragDistance = self.dragDistance + distance( x,y, self.x0, self.y0 )
		if self.dragDistance > 3 then
			self.dragDistance = 0
			canvas:removeTopProp( x, y, z )
		end
	else
		self.dragDistance = 0
		canvas:removeTopProp( x, y, z )
	end
	self.x0 = x
	self.y0 = y
end

--------------------------------------------------------------------
CLASS: DeckListViewer ( mock_edit.EditorEntity )
	:MODEL{}


--------------------------------------------------------------------
CLASS: DeckCanvasEditor()

function DeckCanvasEditor:__init()
	self.targetCanvas        = false
	self.currentDeckBrush    = false
	self.randomEnabled       = false
	self.deckBrush           = DeckCanvasSingleDeckBrush()
	self.eraseBrush          = DeckCanvasEraseBrush()
end

function DeckCanvasEditor:findTargetDeckCanvas()
	local selection = gii.getSelection( 'scene' )
	--find a parent animator
	if #selection ~= 1 then --only single selection allowed( for now )
		return nil
	end

	local ent = selection[1]
	if not isInstance( ent, mock.Entity ) then
		return nil
	end

	while ent do
		local map = ent:getComponent( mock.DeckCanvas )
		if map then return map end
		ent = ent.parent
	end

	return nil
end

function DeckCanvasEditor:setTargetCanvas( c )
	local prevCanvas = self.targetCanvas
	self.targetCanvas = c
end

function DeckCanvasEditor:getTargetCanvas()
	return self.targetCanvas
end

function DeckCanvasEditor:changeDeckSelection( selectionList )
	local selection = gii.listToTable( selectionList or {} )
	self.deckBrush:setDecks( selection )
	self.deckBrush:setInitialScl( self.initialScl )
	self.initialScl = false
end

function DeckCanvasEditor:getBrush()
	return self.deckBrush
end

function DeckCanvasEditor:getEraseBrush()
	return self.eraseBrush
end

function DeckCanvasEditor:pickDeck( canvas, x, y )
	local prop = canvas:findTopProp( x, y )
	if prop then
		local path = prop.deckPath
		self.initialScl = { prop:getScl() }
		gii.changeSelection( 'asset', gii.getAssetNode( path ) )
		gii.app:getModule( 'asset_browser' ):locateAsset( path, false )
	else
		self.initialScl = false
	end

end

function DeckCanvasEditor:startPenTool( id )
	mock_edit.getCurrentSceneView():changeCanvasTool( 'deckcanvas.pen' )
end

function DeckCanvasEditor:clear()
	if not self.targetCanvas then return end
	self.targetCanvas:clear()
	gii.emitPythonSignal( 'entity.modified', ent )
end

function DeckCanvasEditor:toggleToolRandom( enabled )
	self.randomEnabled = enabled
end

function DeckCanvasEditor:wndToModel( x, y )
	local sceneView = mock_edit.getCurrentSceneView()
	local x, y, z = sceneView:wndToWorld( x, y )
	if self.targetCanvas then
		local mx, my, mz = self.targetCanvas:getEntity():getProp('render'):worldToModel( x, y, z )
		return mx, my, mz
	else
		return x, y, z
	end
end

function DeckCanvasEditor:wndToWorld( x, y )
	local sceneView = mock_edit.getCurrentSceneView()
	return sceneView:wndToWorld( x, y )
end


--------------------------------------------------------------------
CLASS: DeckCanvasToolPen ( mock_edit.CanvasTool )
	:MODEL{}

function DeckCanvasToolPen:__init()
	self.pressed = false
	self.action  = false
	self.drawFromPos = { 0, 0 }
	self.dragOffset  = { 0, 0 }
	self.mapping = 'xy'
end

function DeckCanvasToolPen:updateDrawFromPos( x, y )
	self.drawFromPos = { x, y }
end

function DeckCanvasToolPen:getDrawFromPos()
	return unpack( self.drawFromPos )
end

function DeckCanvasToolPen:onMouseDown( btn, x, y )
	if self.pressed then return end
	local inputDevice = self:getInputDevice()
	self.mapping = 'xy'

	if btn == 'left' then 
		if inputDevice:isCtrlDown() then
			if inputDevice:isAltDown() then
				if inputDevice:isShiftDown() then
					self.action = 'flipy'
				else
					self.action = 'flipx'
				end
			else
				self.action = 'auto'
				self.mapping = 'xz'
			end

		elseif inputDevice:isAltDown() then
			self.action = 'pick'

		elseif inputDevice:isMetaDown() then
			self.action = 'add'
			if inputDevice:isCtrlDown() then
				self.mapping = 'xz'
			end
		else
			self.action = 'auto'

		end

		self:_doAction( x, y )

	elseif btn == 'right' then
		self.action = 'remove'
		self:_doAction( x, y )

	else
		self.action = false
	end
	self.pressed = btn
end

function DeckCanvasToolPen:onMouseUp( btn, x, y )
	if self.pressed ~= btn then return end
	self.pressed    = false
	self.targetRoom = false
	self.previousProp = false
	self.action = false
end

function DeckCanvasToolPen:onMouseMove( x, y )
	if not self.pressed then return end
	self:_doAction( x, y, true )
end

function DeckCanvasToolPen:_doAction( x, y, dragging )
	local canvas = editor:getTargetCanvas()
	if not canvas then return false end
			-- return mock_edit.alertMessage( 'message', 'no target deckcanvas selected', 'info' )
		-- end
	local wx, wy = editor:wndToWorld( x, y )
	x, y = canvas:worldToModel( wx, wy )
	-- if canvas:inside( wx, wy ) then
		self:onAction( self.action, canvas, x, y, dragging )
		gii.emitPythonSignal( 'entity.modified', ent )

	-- end
end

function DeckCanvasToolPen:actionMove( action, canvas, x, y, dragging )
	
end

function DeckCanvasToolPen:onAction( action, canvas, x, y, dragging )
	-- if action == 'movez' then
	-- 	if dragging then
	-- 		if self.previousProp then
	-- 			local x0, y0, z0 = unpack( self.propLoc0 )
	-- 			local mx0, my0 =  unpack( self.dragLoc0 )
	-- 			local dx, dy = x - mx0, y - my0
	-- 			self.previousProp:setLoc( x0 + dx, y0, z0 + dy )
	-- 		end
	-- 	else
	-- 		local prop = canvas:findTopProp( x, y )
	-- 		self.previousProp = prop
	-- 		if prop then
	-- 			local x0, y0, z0 = prop:getLoc()
	-- 			self.propLoc0   = { x0, y0, z0 }
	-- 			self.dragLoc0   = { x, y }
	-- 		end
	-- 	end
	-- 	markProtoInstanceOverrided( canvas, 'serializedData' )

	if action == 'add' then
		if dragging then
		else
			local brush = editor:getBrush()
			if brush then
				x, y = canvas:modelToCanvas( x, y, 0, action )
				local output
				if self.mapping == 'xz' then
					output = brush:paint( canvas, x, 0, y, dragging )
				else
					output = brush:paint( canvas, x, y, 0, dragging )
				end
				self.previousProp = output
				if self.initialScl then
					output:setScl( unpack( self.initialScl ) )
				end
				local x0, y0, z0 = prop:getLoc()
				self.propLoc0   = { x0, y0, z0 }
				self.dragLoc0   = { x, y }
				self:updateDrawFromPos( x, y )
				self.action = 'auto'
			end		
		end
		markProtoInstanceOverrided( canvas, 'serializedData' )

	elseif action == 'auto' then
		if dragging then
			x, y = canvas:modelToCanvas( x, y, 0, 'move' )
			if self.previousProp then
				local x0, y0, z0 = unpack( self.propLoc0 )
				local mx0, my0 =  unpack( self.dragLoc0 )
				local dx, dy = x - mx0, y - my0

				if self.mapping == 'xz' then
					self.previousProp:setLoc( x0 + dx, y0, z0 + dy )
				else
					self.previousProp:setLoc( x0 + dx, y0 + dy, z0 )
				end
			end
		else
			local prop = canvas:findTopProp( x, y )
			if not prop then
				x, y = canvas:modelToCanvas( x, y, 0, 'add' )
				if self.mapping == 'xz' then
					prop = editor:getBrush():paint( canvas, x, 0, y, dragging )
				else
					prop = editor:getBrush():paint( canvas, x, y, 0, dragging )
				end
				if not prop then return end
			else
				x, y = canvas:modelToCanvas( x, y, 0, 'move' )
			end
			self.previousProp = prop
			local x0, y0, z0 = prop:getLoc()
			self.propLoc0   = { x0, y0, z0 }
			self.dragLoc0   = { x, y }
			self:updateDrawFromPos( x, y )
		end
		markProtoInstanceOverrided( canvas, 'serializedData' )

	elseif action == 'shift' then --remove

	elseif action == 'remove' then
		editor:getEraseBrush():paint( canvas, x, y, 0, dragging )
		self:updateDrawFromPos( x, y )
		markProtoInstanceOverrided( canvas, 'serializedData' )

	elseif action == 'flipx' then
		local prop = canvas:findTopProp( x, y )
		if ( not dragging ) and prop then
			local sx, sy, sz = prop:getScl()
			prop:setScl( -sx, sy, sz )
		end
		markProtoInstanceOverrided( canvas, 'serializedData' )

	elseif action == 'flipy' then
		local prop = canvas:findTopProp( x, y )
		if ( not dragging ) and prop then
			local sx, sy, sz = prop:getScl()
			prop:setScl( sx, -sy, sz )
		end
		markProtoInstanceOverrided( canvas, 'serializedData' )

	elseif action == 'pick' then --remove
		if not dragging then
			editor:pickDeck( canvas, x, y )
		end

	end
end

mock_edit.registerCanvasTool( 'deckcanvas.pen', DeckCanvasToolPen )


--------------------------------------------------------------------
editor = DeckCanvasEditor()

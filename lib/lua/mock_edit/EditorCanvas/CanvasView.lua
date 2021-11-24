module 'mock_edit'

CLASS: CanvasView ( EditorEntity )

function CanvasView:__init( canvasEnv )
	self.canvasEnv = assert( canvasEnv )
	function canvasEnv.onResize( w, h )
		return self:onCanvasResize( w, h )
	end	

	function canvasEnv.onUpdate( dt )
		return self:onCanvasUpdate( dt )
	end	

	function canvasEnv.preDraw()
		return self:preCanvasDraw()
	end
	local delegate = canvasEnv._delegate
	if delegate then
		delegate:updateHooks()
	end

	--config
	self.gridSnapping = false

	--state
	self.defaultCursor = 'arrow'
	self.cursorOverrided = false

end

function CanvasView:onDestroy()
	local canvasEnv = self.canvasEnv
	canvasEnv.onResize = false
	canvasEnv.onUpdate = false
	canvasEnv.preDraw  = false
	local delegate = canvasEnv._delegate
	if delegate then
		delegate:updateHooks()
	end
end

function CanvasView:onLoad()
	self:initContext()
	self:initAddons()
	self:onInit()
	self:initEntityEventListener()
end

function CanvasView:createCamera( canvasEnv )
	local cameraEntity = EditorEntity()
	local cameraCom    = EditorCanvasCamera( canvasEnv )
	cameraEntity:attach( cameraCom )
	self:addChild( cameraEntity )
	return cameraEntity, cameraCom
end

function CanvasView:initContext()
	self:setName( '__scene_view__' )
	self:initInput()
	self.camera, self.cameraCom = self:createCamera( self.canvasEnv )
end

function CanvasView:initInput()
	local inputDevice = getEditorCanvasInputDevice( self.canvasEnv )
	self:attach( mock.InputScript{ device = inputDevice } )
	self.inputDevice = inputDevice
end

function CanvasView:initAddons()
	self.grid = self:addChild( CanvasGrid() )
	self.navi = self:addChild( CanvasNavigate{ 
			inputDevice = assert( self:getInputDevice() ),
			camera      = self:getCamera()
		} )
	self.toolManager        = self:addChild( CanvasToolManager() )
	self.gizmoManager       = self:addChild( GizmoManager() )
	self.itemManager        = self:addChild( CanvasItemManager() )
	self.pickingManager     = self:addChild( PickingManager() )
	self.pickingManager:setTargetScene( self:getScene() )

end

function CanvasView:initEntityEventListener()
	self:connect( 'scene.entity_event', 'onEntityEvent' )
end

function CanvasView:onInit()
end

function CanvasView:getInputDevice()
	return self.inputDevice
end

function CanvasView:getCamera()
	return self.camera
end

function CanvasView:getCameraZoom()
	return self.camera:getZoom()
end

function CanvasView:getCameraComponent()
	return self.cameraCom
end

function CanvasView:getCenter()
	return self.camera:getWorldLoc()
end

function CanvasView:wndToWorld( x, y )
	return self.cameraCom:wndToWorld( x, y )
end

function CanvasView:addCanvasItem( item )
	self.itemManager:addItem( item )
end

function CanvasView:removeCanvasItem( item )
	self.itemManager:removeItem( item )
end

function CanvasView:changeCanvasTool( name )
	self.toolManager:setTool( name )
end

function CanvasView:getActiveTool()
	return self.toolManager:getActiveTool()
end

function CanvasView:getActiveToolId()
	return self.toolManager:getActiveToolId()
end

function CanvasView:toggleDebugLines()
	self.cameraCom:setShowDebugLines( not self.cameraCom.showDebugLines )
	self:updateCanvas()
end

function CanvasView:onCanvasResize( w, h )
	if self.camera then
		local com = self.camera:getComponent( EditorCanvasCamera )
		if com then 
			-- com:setScreenSize( w, h )
			-- GIIHelper.updateResourceMgr()
			-- com:updateViewport()
		end
	end
	self:updateCanvas()
end

function CanvasView:preCanvasDraw()
	self.toolManager:preCanvasDraw()
	self.itemManager:preCanvasDraw()
	self.gizmoManager:preCanvasDraw()
end

function CanvasView:onCanvasUpdate( dt )
	self.toolManager:onCanvasUpdate( dt )
end

function CanvasView:onSelectionChanged( selection )
	selection = gii.listToTable( selection )
	for child in pairs( self.children ) do
		local onSelectionChanged = child.onSelectionChanged
		if onSelectionChanged then onSelectionChanged( child, selection ) end
	end
	self:updateCanvas()
end

function CanvasView:onEntityEvent( scene, ev, entity, com ) --FIXME: remove this
	if scene ~= self.scene then return end
	for child in pairs( self.children ) do
		local onEntityEvent = child.onEntityEvent
		if onEntityEvent then onEntityEvent( child, ev, entity, com ) end
	end
end


function CanvasView:pick( x, y, pad, returnAll, ignoreEditLock )
	return self.pickingManager:pickPoint( x, y, pad, returnAll, ignoreEditLock ) 
end

function CanvasView:pickRect( x0, y0, x1, y1, pad, returnAll, ignoreEditLock )
	return self.pickingManager:pickRect( x0, y0, x1, y1, pad, returnAll, ignoreEditLock ) 
end

function CanvasView:pickAndSelect( x, y, pad, returnAll, ignoreEditLock )
	local picked = self:pick( x, y, pad, returnAll, ignoreEditLock )
	gii.changeSelection( 'scene', unpack( picked ) )
	return picked
end


--------------------------------------------------------------------
function CanvasView:setGridSize( w, h )
	return self.grid:setSize( w, h )
end

function CanvasView:getGridSize()
	return self.grid:getSize()
end

function CanvasView:getGridWidth()
	return self.grid:getWidth()
end

function CanvasView:getGridHeight()
	return self.grid:getHeight()
end

function CanvasView:setGridWidth( w )
	return self.grid:setWidth( w )
end

function CanvasView:setGridHeight( h )
	return self.grid:setHeight( h )
end

function CanvasView:isGridVisible()
	return self.grid:isVisible()
end

function CanvasView:setGridVisible( vis )
	self.grid:setVisible( vis )
end

function CanvasView:isGridSnapping()
	return self.gridSnapping
end

function CanvasView:setGridSnapping( snapping )
	self.gridSnapping = snapping
end

function CanvasView:snapLoc( x,y,z, activeAxis )
	--2d
	if not self.gridSnapping then return x,y,z end
	local gw, gh = self:getGridSize()
	local x1 = math.floor( x/gw ) * gw
	local y1 = math.floor( y/gh ) * gh
	local dx = x - x1
	if dx > gw*0.5 then
		x1 = x1 + gw
		dx = dx - gw
	end
	local dy = y - y1
	if dy > gh*0.5 then
		y1 = y1 + gh
		dy = dy - gh
	end
	local snapX = true --dx*dx < gw*gw*0.09
	local snapY = true --dy*dy < gh*gh*0.09
	if activeAxis == 'x' then
		snapY = true
	elseif activeAxis == 'y' then
		snapX = true
	end
	if snapX and snapY then
		return x1,y1,z
	else
		return x,y,z
	end

end


function CanvasView:isGizmoVisible()
	return self.gizmoManager:isGizmoVisible()
end

function CanvasView:setGizmoVisible( vis )
	self.gizmoManager:setGizmoVisible( vis )
end

function CanvasView:updateGizmoVisibility()
	self.gizmoManager:updateGizmoVisibility()
end

function CanvasView:resetGizmoVisibility()
	self.gizmoManager:resetGizmoVisibility()
end

function CanvasView:refreshGizmo()
	self.gizmoManager:refresh()
end
--------------------------------------------------------------------
function CanvasView:updateCanvas( forced, no_sim )
	if self.canvasEnv.updateCanvas then
		return self.canvasEnv.updateCanvas( forced, no_sim )
	end
end

function CanvasView:scheduleUpdate()
end

function CanvasView:setCursor( id )
	if id then
		self.cursorOverrided = true
		return self.canvasEnv.setCursor( id )
	else
		self.cursorOverrided = false
		return self.canvasEnv.setCursor( self.defaultCursor or 'arrow' )
	end
end

function CanvasView:resetCursor()
	return self:setCursor( false )
end

function CanvasView:setDefaultCursor( id )
	self.defaultCursor = id or 'arrow'
	if not self.cursorOverrided then
		return self:resetCursor()
	end
end

function CanvasView:hideCursor()
	return self.canvasEnv.hideCursor()
end

function CanvasView:showCursor()
	return self.canvasEnv.showCursor()
end

function CanvasView:setCursorPos( x, y )
	return self.canvasEnv.setCursorPos( x, y )
end

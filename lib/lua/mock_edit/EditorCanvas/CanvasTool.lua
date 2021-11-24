module 'mock_edit'


local CanvasToolRegistry = {}
--------------------------------------------------------------------
function registerCanvasTool( id, clas )
	CanvasToolRegistry[ id ] = clas
end

--------------------------------------------------------------------
CLASS: CanvasToolManager ( SceneEventListener )
	:MODEL{}

function CanvasToolManager:__init( option )
	self.option = option or {}
	self.activeTool = false
end

function CanvasToolManager:onLoad()	
end

function CanvasToolManager:getCurrentView()
	return self.parent
end

function CanvasToolManager:getView()
	return self.parent
end

function CanvasToolManager:getActiveTool()
	return self.activeTool
end

function CanvasToolManager:getActiveToolId()
	return self.activeTool and self.activeTool.__toolId
end

function CanvasToolManager:setTool( id )
	--TODO: allow tool cache??
	local toolClass = CanvasToolRegistry[ id ]
	if not toolClass then
		_warn( 'no tool found', id )
		return false
	end

	local prevTool = self.activeTool
	if prevTool then
		prevTool:destroyWithChildrenNow()
	end

	local tool = toolClass()
	tool.__toolId = id
	tool:installInput( self.parent:getInputDevice() )	
	self.activeTool = tool
	self:addChild( tool )
	self:getView():updateCanvas()
end

function CanvasToolManager:onSelectionChanged( selection )
	if self.activeTool then
		self.activeTool:onSelectionChanged( selection )
	end
end

function CanvasToolManager:onEntityEvent( ev, entity, com )
	if self.activeTool then
		self.activeTool:onEntityEvent( ev, entity, com )
	end
end

function CanvasToolManager:onCanvasUpdate( dt )
	if self.activeTool then
		self.activeTool:onCanvasUpdate( dt )
	end
end

function CanvasToolManager:preCanvasDraw()
	if self.activeTool then
		self.activeTool:preCanvasDraw()
	end
end

--------------------------------------------------------------------
--------------------------------------------------------------------
CLASS: CanvasTool( SceneEventListener )

function CanvasTool:__init()
	self.items = {}
end

function CanvasTool:getIcon()
	return false
end

function CanvasTool:onLoad()
end

function CanvasTool:installInput( inputDevice )
	local inputDevice = inputDevice or self:getInputDevice()
	assert( inputDevice )
	self:attach( mock.InputScript{ 
			device = inputDevice
		} )
end

function CanvasTool:getInputDevice()
	return self:getCurrentView():getInputDevice()
end

--TODO:use more unified framework for editor canvas scene
function CanvasTool:getCurrentView()
	return self.parent:getView()
end

function CanvasTool:updateCanvas()
	self:getCurrentView():updateCanvas()
end

function CanvasTool:updateAllViews()
	--TODO:
end

function CanvasTool:onCanvasUpdate( dt )
end

function CanvasTool:preCanvasDraw()
end

function CanvasTool:onActivate()
end

function CanvasTool:onDeactivate()
end

function CanvasTool:addCanvasItem( item )
	local view = self:getCurrentView()
	view:addCanvasItem( item )
	self.items[ item ] = true
	item.tool = self
	return item
end

function CanvasTool:removeCanvasItem( item )
	if item then
		item:destroyWithChildrenNow()
		self.items[ item ] = nil
	end
end

function CanvasTool:clearCanvasItems()
	for item in pairs( self.items ) do
		item:destroyWithChildrenNow()
	end
	self.items = {}
end

function CanvasTool:onDestroy()
	self:clearCanvasItems()
end

function CanvasTool:getSelection( key )
	return gii.getSelection( key or 'scene' )
end

function CanvasTool:getOneSelection( clas )
	local selection = self:getSelection( 'scene' )
	if clas then
		for i, obj in ipairs( selection ) do
			if isInstance( obj, clas ) then
				return obj
			end
		end
		return nil
	else
		return selection[ 1 ]
	end
end

function CanvasTool:findTopLevelEntities( entities )
	local found = {}
	if not entities then return false end
	for e in pairs( entities ) do
		local p = e.parent
		local isTop = true
		while p do
			if entities[ p ] then isTop = false break end
			p = p.parent
		end
		if isTop then found[e] = true end
	end
	return found
end

function CanvasTool:onSelectionChanged( selection )
end


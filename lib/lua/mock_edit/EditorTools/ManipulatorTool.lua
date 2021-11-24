module 'mock_edit'


--------------------------------------------------------------------
local function _collectManipulatorBuilders( e, collected )
	if not e:isVisible() then return end
	-- if e:isEditLocked() then return end
	local onBuildManipulator = e.onBuildManipulator
	if type( onBuildManipulator ) == 'function' then
		collected[ e ] = true
	end
	for com in pairs( e.components ) do
		if not com.FLAG_INTERNAL then
			local onBuildManipulator = com.onBuildManipulator
			if type( onBuildManipulator ) == 'function' then
				collected[ com ] = true
			end
		end
	end
end

--------------------------------------------------------------------
CLASS: ManipulatorTool ( SelectionTool )
	:MODEL{}

function ManipulatorTool:__init()
	self.manipulators = {}
end

function ManipulatorTool:onLoad()
	ManipulatorTool.__super.onLoad( self )
	self:setRectPickingEnabled( false )
	self:rebuildManipulators()
end

function ManipulatorTool:onSelectionChanged( selection )
	self:rebuildManipulators()
end

function ManipulatorTool:clearManipulators()
	for manipulator in pairs( self.manipulators ) do
		manipulator:destroyAllNow()
	end
	self.manipulators = {}
end

function ManipulatorTool:rebuildManipulators()
	self:clearManipulators()
	local selection = self:getSelection()
	local tobuild = {}
	for i, e in ipairs( selection ) do
		if isInstance( e, mock.Entity ) then 
			_collectManipulatorBuilders( e, tobuild )
		end
	end

	for obj, builder in pairs( tobuild ) do
		self:addManipulator( obj )
	end
	self:updateCanvas()
end

function ManipulatorTool:addManipulator( obj )
	local manipulator = obj:onBuildManipulator()
	if not manipulator then return end
	manipulator:setTarget( obj )
	self:addChild( manipulator )
	self.manipulators[ manipulator ] = true
end

function ManipulatorTool:removeManipulator( obj )
	for manipulator in pairs( self.manipulators ) do
		if manipulator:getTarget() == obj then
			manipulator:destroyAllNow()
			self.manipulators[ manipulator ] = nil
			return true
		end
	end
	return false
end

function ManipulatorTool:onEntityEvent( ev, entity, com )
	if ev == 'detach' then
		self:removeManipulator( com )
	elseif ev == 'attach' then
		if isComponentSelected( com ) then
			local onBuildManipulator = com.onBuildManipulator
			if type( onBuildManipulator ) == 'function' then
				self:addManipulator( com )
			end
		end
	end
end

registerCanvasTool( 'manipulator', ManipulatorTool )

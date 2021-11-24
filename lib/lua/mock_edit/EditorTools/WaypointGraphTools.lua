module 'mock_edit'

--------------------------------------------------------------------
CLASS: WapypointGraphToolCommon ( mock_edit.CanvasTool )

function WapypointGraphToolCommon:onLoad()
	WapypointGraphToolCommon.__super.onLoad( self )
	self.currentGraph = false
	self.currentGraphContainer = false
	self:updateSelection()
	self.action = false
	self.actionButton = false
end

function WapypointGraphToolCommon:onSelectionChanged( selection )
	self:updateSelection()
end

function WapypointGraphToolCommon:updateSelection()
	self.currentGraph = false
	self.currentGraphContainer = false
	local selection = self:getSelection()
	for i, e in ipairs( selection ) do
		if isInstance( e, mock.Entity ) then 
			local container = e:getComponent( mock.WaypointGraphContainer )
			if container then
				self.currentGraph = container:getGraph()
				self.currentGraphContainer = container
				return
			end
		end
	end

end

function WapypointGraphToolCommon:wndToGraph( x, y )
	x, y = self:wndToWorld( x, y )
	x, y = self.currentGraphContainer:getEntity():worldToModel( x, y )
	return x, y 
end


--------------------------------------------------------------------
CLASS: WapypointGraphToolMain ( WapypointGraphToolCommon )

function WapypointGraphToolMain:__init()
	self.tmpWaypoint = mock.Waypoint()
	self.connectionType = 'forcelink'
end

function WapypointGraphToolMain:onMouseDown( btn, x, y )
	if not self.currentGraph then return end
	if self.action then return end
	self.actionButton = btn

	if btn == 'left' then
		if self:getInputDevice():isShiftDown() then
			self.action = 'add_link'
		elseif self:getInputDevice():isCtrlDown() then
			self.action = 'add_node'
		else
			self.action = 'move_node'
		end
	elseif btn == 'right' then
		if self:getInputDevice():isShiftDown() then
			self.action = 'remove_link'
		elseif self:getInputDevice():isCtrlDown() then
			self.action = 'remove_node'
		else
			self.action = false
		end
	end

	if self.action then
		x, y = self:wndToGraph( x, y )
		return self:onActionStart( self.action, x, y )
	end

end

function WapypointGraphToolMain:onMouseMove( x, y )
	if not self.action then return end
	x, y = self:wndToGraph( x, y )
	self:onActionDrag( self.action, x, y )
end

function WapypointGraphToolMain:onMouseUp( btn, x, y )
	if not self.action then return end
	if not self.actionButton == btn then return end
	x, y = self:wndToGraph( x, y )
	self:onActionStop( self.action, x, y )
	self.action = false
	self.actionButton = false
end


function WapypointGraphToolMain:onActionStart( action, x, y )
	if action == 'add_node' then
		local p = self.currentGraph:addWaypoint()
		p:setLoc( x, y )
		self.currentWaypoint = p
		self.currentWaypoint.selected = true
		self.currentWaypointDragOffset = { 0, 0 }
	else
		local p = self.currentGraph:findWaypointByLoc( x, y, 20 )		
		if not p then return end

		if action == 'move_node' then
			self.currentWaypoint = p
			self.currentWaypoint.selected =true
			local px, py = p:getLoc()
			local dx, dy = px - x, py - y
			self.currentWaypointDragOffset = { dx, dy }

		elseif action == 'remove_node' then
			self.currentGraph:removeWaypoint( p )

		elseif action == 'add_link' or action == 'remove_link' then
			self.tmpWaypoint:setLoc( x, y )
			self.currentWaypoint = p
			self.currentGraph:_addTmpConnection( self.tmpWaypoint, p, self.connectionType )

		end

	end
	self:updateCanvas()	
end

function WapypointGraphToolMain:onActionDrag( action, x, y )
	if action == 'add_node' or action == 'move_node' then
		if not self.currentWaypoint then return end
		local ox, oy = unpack( self.currentWaypointDragOffset )
		self.currentWaypoint:setLoc( x + ox, y + oy )

	elseif action == 'add_link' or action == 'remove_link' then
		if not self.currentWaypoint then return end
		self.tmpWaypoint:setLoc( x, y )

	end
	self:updateCanvas()
end

function WapypointGraphToolMain:onActionStop( action, x, y )
	if action == 'add_node' or action == 'move_node' then
		if not self.currentWaypoint then return end
		self.currentWaypoint.selected = false
		self.currentWaypoint = false

	elseif action == 'remove_link' then
		if not self.currentWaypoint then return end
		local p = self.currentGraph:findWaypointByLoc( x, y, 20 )
		if p then
			self.currentWaypoint:removeNeighbour( p )
		end
		self.currentGraph:_clearTmpConnections()
		self.currentWaypoint = false
			
	elseif action == 'add_link' then
		if not self.currentWaypoint then return end
		local p = self.currentGraph:findWaypointByLoc( x, y, 20 )
		if p then
			self.currentWaypoint:addNeighbour( p, self.connectionType )
		end
		self.currentGraph:_clearTmpConnections()
		self.currentWaypoint = false

	end

	self:updateCanvas()	
end



--------------------------------------------------------------------
registerCanvasTool( 'waypoint_tool',      WapypointGraphToolMain )
-- registerCanvasTool( 'waypoint_forcelink', WapypointGraphToolForceLink )
-- registerCanvasTool( 'waypoint_nolink',    WapypointGraphToolNoLink )

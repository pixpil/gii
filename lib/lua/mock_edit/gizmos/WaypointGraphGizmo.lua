module 'mock_edit'

addColor( 'waypoint', hexcolor( '#47beff', 1 ) )
addColor( 'waypoint_connection', hexcolor( '#f2ffff', 1 ) )
addColor( 'waypoint_nolink',     hexcolor( '#ff2d00', 1 ) )
addColor( 'waypoint_forcelink',  hexcolor( '#53ee00', 1 ) )

addColor( 'waypoint-selected', hexcolor( '#ffff7a', 1 ) )

--------------------------------------------------------------------

CLASS: WaypointGraphGizmo( Gizmo )
function WaypointGraphGizmo:__init( container )
	self.graphContainer = container
	self.graph = container:getGraph()
	self.transform = MOAITransform.new()
	inheritTransform( self.transform, container._entity:getProp( 'physics' ) )
end

function WaypointGraphGizmo:onLoad()
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end


local size = 8

function WaypointGraphGizmo:onDraw()
	GIIHelper.setVertexTransform( self.transform )
	--TODO: occulusion
	--connections
	local graph = self.graph
	local waypoints = graph.waypoints
	applyColor 'waypoint_connection'
	for i, p in ipairs( waypoints ) do
		for neighbour in pairs( p.neighbours ) do
			if neighbour.nodeId > i then
				self:drawConnection( p, neighbour )	
			end
		end
	end

	--dummy connection
	for key, conn in pairs( graph.tmpConnections ) do
		local p1, p2, ctype = unpack( conn )
		self:drawConnection( p1, p2, ctype )
	end
	
	--waypoints
	for i, p in ipairs( waypoints ) do
		local x, y = p:getLoc()
		if p.selected then
			applyColor 'waypoint-selected'
		else
			applyColor 'waypoint'
		end
		MOAIDraw.fillCircle( x, y, size )
	end

end

function WaypointGraphGizmo:drawConnection( p0, p1, ctype )
	local x0, y0 = p0:getLoc()
	local x1, y1 = p1:getLoc()
	
	if not ctype then
		ctype = p0.neighbours[ p1 ]
	end

	if ctype == 'nolink' then
		applyColor 'waypoint_nolink'
	elseif ctype == 'forcelink' then
		applyColor 'waypoint_forcelink'
	else
		applyColor 'waypoint_connection'
	end
	MOAIDraw.drawLine( x0, y0, x1, y1 )
end

function WaypointGraphGizmo:getPickingTarget()
	return self.graphContainer._entity
end

function WaypointGraphGizmo:isPickable()
	return false
end


--------------------------------------------------------------------
--Install
mock.WaypointGraphContainer.onBuildSelectedGizmo = function( self )
	return WaypointGraphGizmo( self )
end

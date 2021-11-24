module 'mock_edit'

addColor( 'physics_gizmo', hexcolor( '#ff2514', 0.5) )
addColor( 'physics_gizmo_selected', hexcolor( '#ff8800', 1.0) )
addColor( 'physics_gizmo_inactive', hexcolor( '#993a31', 0.3) )

--------------------------------------------------------------------
CLASS: PhysicsShapeGizmo( Gizmo )
function PhysicsShapeGizmo:__init( shape )
	self.target = shape
	self.color = getColorT( 'physics_gizmo' )
end

function PhysicsShapeGizmo:onLoad()
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end

function PhysicsShapeGizmo:onInit( target )
	local prop0 = self:getProp()
	local prop1 = target._entity:getProp( 'physics' )
	local prop2 = target._entity:getProp( 'render' )
	inheritLoc( prop0, prop1 )
	if prop2:getClassName() == 'EWPropRenderTransform' then
		prop0:setAttrLink( MOAIProp.ATTR_Y_LOC, prop1, MOAIProp.ATTR_WORLD_Z_LOC )
	end
end

function PhysicsShapeGizmo:onSelectStateChanged( target, state )
	if state == 'selected' then
		if target.active then
			self.color = getColorT( 'physics_gizmo_selected' )
		else
			self.color = getColorT( 'physics_gizmo_inactive' )
		end
	else
		if target.active then
			self.color = getColorT( 'physics_gizmo' )
		else
			self.color = getColorT( 'physics_gizmo_inactive' )
		end
	end
end

function PhysicsShapeGizmo:onDraw()
end

function PhysicsShapeGizmo:getPickingTarget()
	return self.target._entity
end

function PhysicsShapeGizmo:isPickable()
	return true
end



--------------------------------------------------------------------
CLASS: PhysicsShapeBoxGizmo( PhysicsShapeGizmo )

function PhysicsShapeBoxGizmo:__init( shape )
end

function PhysicsShapeBoxGizmo:onDraw()
	local shape = self.target
	local verts = shape:getLocalVerts()
	MOAIDraw.setPenWidth(1)
	MOAIDraw.setPenColor( unpack( self.color ) )
	table.insert( verts, verts[1] )
	table.insert( verts, verts[2] )
	MOAIDraw.drawLine( verts )
end



function PhysicsShapeBoxGizmo:onGetRect()
	local shape = self.target
	local x, y = shape:getLoc()
	local w, h = shape.w, shape.h
	return -0.5*w + x, -0.5*h + y, 0.5*w + x, 0.5*h + y
end


function PhysicsShapeBoxGizmo:getPickingProp()
	return self.drawScript:getMoaiProp()
end

--Install
mock.PhysicsShapeBox.onBuildGizmo = function( self )
	return PhysicsShapeBoxGizmo( self )
end
mock.PhysicsShapeBevelBox.onBuildGizmo = function( self )
	return PhysicsShapeBoxGizmo( self )
end


--------------------------------------------------------------------
CLASS: PhysicsShapeCircleGizmo( PhysicsShapeGizmo )

function PhysicsShapeCircleGizmo:__init( shape )
end

function PhysicsShapeCircleGizmo:onDraw()
	local shape = self.target
	local x, y = shape:getLoc()
	local radius = shape.radius

	MOAIDraw.setPenColor( unpack( self.color ) )
	MOAIDraw.setPenWidth(1)
	
	MOAIDraw.drawCircle( x, y, radius )
end


function PhysicsShapeCircleGizmo:onGetRect()
	local shape = self.target
	local x, y = shape:getLoc()
	local radius = shape.radius
	return -radius+x, -radius+y, radius+x, radius+y
end


function PhysicsShapeCircleGizmo:getPickingProp()
	return self.drawScript:getMoaiProp()
end

--Install
mock.PhysicsShapeCircle.onBuildGizmo = function( self )
	return PhysicsShapeCircleGizmo( self )
end



--------------------------------------------------------------------
CLASS: PhysicsShapePieGizmo( PhysicsShapeGizmo )

function PhysicsShapePieGizmo:__init( shape )
end

function PhysicsShapePieGizmo:onDraw()
	local shape = self.target
	MOAIDraw.setPenColor( unpack( self.color ) )
	MOAIDraw.setPenWidth(1)
	local verts = shape:getLocalVerts()
	table.insert( verts, verts[1] )
	table.insert( verts, verts[2] )
	MOAIDraw.drawLine( verts )
end

function PhysicsShapePieGizmo:onGetRect()
	local aabb = self.target.aabb
	if not aabb then
		return 0,0,0,0,0,0
	else
		return unpack( aabb )
	end
end

--Install
mock.PhysicsShapePie.onBuildGizmo = function( self )
	return PhysicsShapePieGizmo( self )
end



--------------------------------------------------------------------
CLASS: PhysicsShapePolygonGizmo( PhysicsShapeGizmo )

function PhysicsShapePolygonGizmo:__init( shape )
end

function PhysicsShapePolygonGizmo:onDraw()
	local shape = self.target
	local x, y = shape:getLoc()
	local w, h = shape.w, shape.h
	local rot  = shape.rotation
	-- self.transform:setLoc( x, y )
	-- self.transform:setRot( 0,0, rot )
	-- GIIHelper.setVertexTransform( self.transform )

	MOAIDraw.setPenColor( unpack( self.color ) )
	MOAIDraw.setPenWidth(1)
	
	local verts = table.simplecopy( shape:getVerts() )
	table.insert( verts, verts[1] )
	table.insert( verts, verts[2] )
	MOAIDraw.drawLine( verts )
end

function PhysicsShapePolygonGizmo:onGetRect()
	return unpack( self.target.aabb )
end

--Install
mock.PhysicsShapePolygon.onBuildGizmo = function( self )
	return PhysicsShapePolygonGizmo( self )
end

--------------------------------------------------------------------
CLASS: PhysicsShapeChainGizmo( PhysicsShapeGizmo )

function PhysicsShapeChainGizmo:__init( shape )
end

function PhysicsShapeChainGizmo:onDraw()
	local shape = self.target

	MOAIDraw.setPenColor( unpack( self.color ) )
	MOAIDraw.setPenWidth(1)
	
	local verts = table.simplecopy( shape:getVerts() )
	if shape:isLooped() then
		table.insert( verts, verts[1] )
		table.insert( verts, verts[2] )
	end
	MOAIDraw.drawLine( verts )
end

function PhysicsShapeChainGizmo:onGetRect()
	return unpack( self.target.boundRect )
end

--Install
mock.PhysicsShapeChain.onBuildGizmo = function( self )
	return PhysicsShapeChainGizmo( self )
end
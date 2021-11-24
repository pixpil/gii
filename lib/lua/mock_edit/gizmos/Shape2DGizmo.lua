module 'mock_edit'

addColor( 'shape_gizmo_inactive', hexcolor( '#8c8c8c', 0.4) )
addColor( 'shape_gizmo', hexcolor( '#ffffff', 0.7) )

--------------------------------------------------------------------
CLASS: Shape2DGizmo( Gizmo )
function Shape2DGizmo:__init( shape )
	self.shape = shape
	self.transform = MOAITransform.new()
	inheritTransform( self.transform, shape._entity:getProp( 'physics' ) )
end

function Shape2DGizmo:onLoad()
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end

function Shape2DGizmo:onDraw()
end

function Shape2DGizmo:getPickingTarget()
	return self.shape._entity
end

function Shape2DGizmo:isPickable()
	return false
end



--------------------------------------------------------------------
CLASS: ShapeRectGizmo( Shape2DGizmo )

function ShapeRectGizmo:__init( shape )
end

function ShapeRectGizmo:onDraw()
	local shape = self.shape
	local x, y = shape:getLoc()
	local w, h = shape.w, shape.h
	local rot  = shape.rotation
	self.transform:setLoc( x, y )
	self.transform:setRot( 0,0, rot )
	GIIHelper.setVertexTransform( self.transform )

	applyColor( shape.active and 'shape_gizmo' or 'shape_gizmo_inactive' )
	MOAIDraw.setPenWidth(1)
	
	MOAIDraw.drawRect( -0.5*w, -0.5*h, 0.5*w, 0.5*h )
end

function ShapeRectGizmo:onGetRectX()
	local shape = self.shape
	local x, y = shape:getLoc()
	local w, h = shape.w, shape.h
	return -0.5*w, -0.5*h, 0.5*w, 0.5*h
end


function ShapeRectGizmo:getPickingProp()
	return self.drawScript:getMoaiProp()
end

--Install
mock.ShapeRect.onBuildGizmo = function( self )
	return ShapeRectGizmo( self )
end


--------------------------------------------------------------------
CLASS: ShapeCircleGizmo( Shape2DGizmo )

function ShapeCircleGizmo:__init( shape )
end

function ShapeCircleGizmo:onDraw()
	local shape = self.shape
	local x, y = shape:getLoc()
	local radius = shape.radius
	self.transform:setLoc( x, y )
	GIIHelper.setVertexTransform( self.transform )

	applyColor( shape.active and 'shape_gizmo' or 'shape_gizmo_inactive' )
	MOAIDraw.setPenWidth(1)
	
	MOAIDraw.drawCircle( 0,0, radius )
end


function ShapeCircleGizmo:onGetRectX()
	local shape = self.shape
	local x, y = shape:getLoc()
	local radius = shape.radius
	return -0.5*radius, -0.5*radius, 0.5*radius, 0.5*radius
end


function ShapeCircleGizmo:getPickingProp()
	return self.drawScript:getMoaiProp()
end

--Install
mock.ShapeCircle.onBuildGizmo = function( self )
	return ShapeCircleGizmo( self )
end



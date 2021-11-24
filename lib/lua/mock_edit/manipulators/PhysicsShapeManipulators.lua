module 'mock_edit'


--------------------------------------------------------------------
CLASS: PhysicsShapeManipulatorBox ( Manipulator )

function PhysicsShapeManipulatorBox:onLoad()
	local shape = self:getTarget()
	local rect = self:addCanvasItem( CanvasItemEditableRect() )
	function rect:onPullAttr() --x,y,radius
		local x, y = shape:getLoc()
		local w, h = shape:getSize()
		local rot  = shape:getRotation()
		x, y = shape:modelToWorld( x, y )
		return x, y, w, h, rot
	end

	function rect:onPushAttr( x,y, w,h,  rot )
		shape:forceUpdate()
		local x, y = shape:worldToModel( x, y )
		shape:setLoc( x, y )
		shape:setSize( w, h )
		shape:setRotation( rot )
		gii.emitPythonSignal( 'entity.modified', shape._entity )
		mock.markProtoInstanceFieldsOverrided(
			shape, 
			'loc', 'w', 'h'
		)
	end

	rect:updateShape()
end


--------------------------------------------------------------------
CLASS: PhysicsShapeManipulatorCircle ( Manipulator )

function PhysicsShapeManipulatorCircle:onLoad()
	local shape = self:getTarget()
	local circle = self:addCanvasItem( CanvasItemEditableCircle() )
	function circle:onPullAttr() --x,y,radius
		local x, y = shape:getLoc()
		x, y = shape:modelToWorld( x, y )
		local r    = shape:getRadius()
		return x, y, r
	end

	function circle:onPushAttr( x,y, radius )
		shape:forceUpdate()
		local x, y = shape:worldToModel( x, y )
		shape:setLoc( x, y )
		shape:setRadius( radius )
		gii.emitPythonSignal( 'entity.modified', shape._entity )
		mock.markProtoInstanceFieldsOverrided(
			shape, 
			'loc',
			'radius'
		)
	end

	circle:updateShape()

end


--------------------------------------------------------------------
CLASS: PhysicsShapeManipulatorPolygon ( Manipulator )

function PhysicsShapeManipulatorPolygon:onLoad()
	local geom = self:getTarget()
	local poly = self:addCanvasItem( CanvasItemEditablePolygon() )
	function poly:onPullAttr() --verts
		local verts = geom:getVerts()
		local wverts = {}
		local ent = geom._entity
		for i = 1, #verts, 2 do
			local x, y = verts[ i ], verts[ i + 1 ]
			x, y = ent:modelToWorld( x, y )
			wverts[ i ], wverts[ i + 1 ]  = x, y
		end
		return wverts
	end

	function poly:onPushAttr( verts )
		geom:forceUpdate()
		local ent = geom._entity
		local lverts = {}
		for i = 1, #verts, 2 do
			local x, y = verts[ i ], verts[ i + 1 ]
			x, y = ent:worldToModel( x, y )
			lverts[ i ], lverts[ i + 1 ]  = x, y
		end
		geom:setVerts( lverts )
		gii.emitPythonSignal( 'entity.modified', ent )
		mock.markProtoInstanceFieldsOverrided(
			geom, 
			'verts'
		)
	end

	poly:updateShape()

end


--------------------------------------------------------------------
CLASS: PhysicsShapeManipulatorChain ( Manipulator )

function PhysicsShapeManipulatorChain:onLoad()
	local geom = self:getTarget()
	local strip = self:addCanvasItem( CanvasItemEditableLineStrip() )
	strip.looped = geom.looped
	function strip:onPullAttr() --verts
		local verts = geom:getVerts()
		local wverts = {}
		local ent = geom._entity
		for i = 1, #verts, 2 do
			local x, y = verts[ i ], verts[ i + 1 ]
			x, y = ent:modelToWorld( x, y )
			wverts[ i ], wverts[ i + 1 ]  = x, y
		end
		local looped = geom:isLooped()
		return wverts, looped
	end

	function strip:onPushAttr( verts, looped )
		geom:forceUpdate()
		local ent = geom._entity
		local lverts = {}
		for i = 1, #verts, 2 do
			local x, y = verts[ i ], verts[ i + 1 ]
			x, y = ent:worldToModel( x, y )
			lverts[ i ], lverts[ i + 1 ]  = x, y
		end
		geom.looped = looped
		geom:setVerts( lverts )
		gii.emitPythonSignal( 'entity.modified', ent )
		mock.markProtoInstanceFieldsOverrided(
			geom, 
			'verts'
		)
	end

	strip:updateShape()

end


---------------------------------------------------------------------
--Install
function mock.PhysicsShapeBox:onBuildManipulator()
	return PhysicsShapeManipulatorBox()
end

function mock.PhysicsShapeBevelBox:onBuildManipulator()
	return PhysicsShapeManipulatorBox()
end

function mock.PhysicsShapeCircle:onBuildManipulator()
	return PhysicsShapeManipulatorCircle()
end

function mock.PhysicsShapePolygon:onBuildManipulator()
	return PhysicsShapeManipulatorPolygon()
end

function mock.PhysicsShapeChain:onBuildManipulator()
	return PhysicsShapeManipulatorChain()
end

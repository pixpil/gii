module 'mock_edit'


--------------------------------------------------------------------
CLASS: GeometryRectManipulator ( Manipulator )

function GeometryRectManipulator:onLoad()
	local geom = self:getTarget()
	local rect = self:addCanvasItem( CanvasItemEditableRect() )
	function rect:onPullAttr() --x,y,radius
		local ent = geom._entity
		ent:forceUpdate()
		local x, y = 0,0
		local w, h = geom:getSize()
		local sx, sy = geom:getWorldScl()
		w = w * sx
		h = h * sy
		x, y = ent:modelToWorld( x, y )
		return x, y, w, h, 0
	end

	function rect:onPushAttr( x,y, w,h,  rot )
		local ent = geom._entity
		ent:forceUpdate()
		--FIXME: translation when rotation/scale is not ident causes MADNESS
		local sx, sy = geom:getWorldScl()
		local x0, y0 = ent:getWorldLoc()
		ent:setWorldLoc( x, y )
		local dx = x - x0
		local dy = y - y0
		geom:setSize( w/sx, h/sy )
		gii.emitPythonSignal( 'entity.modified', ent )
		mock.markProtoInstanceFieldsOverrided(
			geom, 
			'w', 'h'
		)
		if dx ~= 0 or dy ~= 0 then
			mock.markProtoInstanceFieldsOverrided(
				ent, 
				'loc'
			)
		end
	end

	rect:updateShape()
end


--------------------------------------------------------------------
CLASS: GeometryCircleManipulator ( Manipulator )

function GeometryCircleManipulator:onLoad()
	local geom = self:getTarget()
	local circle = self:addCanvasItem( CanvasItemEditableCircle() )
	function circle:onPullAttr() --x,y,radius
		local x, y = geom:getLoc()
		x, y = geom:getWorldLoc( x, y )
		local radius = geom:getRadius()
		return x, y, radius
	end

	function circle:onPushAttr( x,y, radius )
		geom:forceUpdate()
		local ent = geom._entity
		ent:setWorldLoc( x, y )
		geom:setRadius( radius )
		gii.emitPythonSignal( 'entity.modified', ent )
		mock.markProtoInstanceFieldsOverrided(
			geom, 
			'radius'
		)
		if dx ~= 0 or dy ~= 0 then
			mock.markProtoInstanceFieldsOverrided(
				ent, 
				'loc'
			)
		end
	end

	circle:updateShape()

end

--------------------------------------------------------------------
CLASS: GeometryLineStripManipulator ( Manipulator )

function GeometryLineStripManipulator:onLoad()
	local geom = self:getTarget()
	local strip = self:addCanvasItem( CanvasItemEditableLineStrip() )
	strip.looped = geom.looped
	strip.showLine = self.showLine ~= false

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
function mock.GeometryRect:onBuildManipulator()
	return GeometryRectManipulator()
end

function mock.GeometryCircle:onBuildManipulator()
	return GeometryCircleManipulator()
end

function mock.GeometryPolygon:onBuildManipulator()
	local m = GeometryLineStripManipulator()
	-- m.showLine = false
	return m
end

function mock.GeometryLineStrip:onBuildManipulator()
	local m = GeometryLineStripManipulator()
	-- m.showLine = false
	return m
end


function mock.GeometryCatmullRomCurve:onBuildManipulator()
	local m = GeometryLineStripManipulator()
	-- m.showLine = false
	return m
end

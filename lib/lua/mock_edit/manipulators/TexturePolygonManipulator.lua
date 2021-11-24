module 'mock_edit'
--------------------------------------------------------------------
CLASS: TexturePolygonManipulator ( Manipulator )

function TexturePolygonManipulator:onLoad()
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
function mock.TexturePolygon:onBuildManipulator()
	return TexturePolygonManipulator()
end

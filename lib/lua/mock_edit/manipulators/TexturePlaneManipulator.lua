module 'mock_edit'

CLASS: TextureRectManipulator ( mock_edit.Manipulator )

function TextureRectManipulator:onLoad()
	local plane = self:getTarget()
	local rect = self:addCanvasItem( mock_edit.CanvasItemEditableRect() )
	rect.filled = false
	function rect:onPullAttr() --x,y,radius
		local ent = plane._entity
		ent:forceUpdate()
		local x, y = 0,0
		local w, h = plane:getWorldSize()
		x, y = ent:modelToWorld( x, y )
		return x, y, w, h, 0
	end

	function rect:onPushAttr( x,y, w,h,  rot )
		local ent = plane._entity
		ent:forceUpdate()
		local x0, y0 = ent:getWorldLoc()
		if x0 ~= x or y0 ~= y then
			ent:setWorldLoc( x, y )
			mock.markProtoInstanceFieldsOverrided(
				ent, 
				'loc'
			)
		end
		plane:setWorldSize( w, h )
		gii.emitPythonSignal( 'entity.modified', ent )
		mock.markProtoInstanceFieldsOverrided(
			plane, 
			'size'
		)		
	end

	rect:updateShape()
end

function mock.TexturePlane:onBuildManipulator()
	return TextureRectManipulator()
end

updateAllSubClasses( mock.TexturePlane )
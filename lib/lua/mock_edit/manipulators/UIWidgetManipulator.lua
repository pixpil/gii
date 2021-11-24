module 'mock_edit'

CLASS: UIWidgetManipulator ( mock_edit.Manipulator )

function UIWidgetManipulator:onLoad()
	local widget = self:getTarget()
	local rect = self:addCanvasItem( mock_edit.CanvasItemEditableRect() )
	rect.filled = false
	function rect:onPullAttr() --x,y,w,h
		widget:forceUpdate()
		local x, y = 0,0
		local w, h = widget:getSize()
		x, y = widget:modelToWorld( x, y )
		return x + w/2, y - h/2, w, h
	end

	function rect:onPushAttr( x,y, w,h,  rot )
		widget:forceUpdate()
		x = x - w/2
		y = y + h/2
		local dx, dy = widget:worldToModel( x, y )
		widget:addLoc( dx, dy, 0 )
		widget:setSize( w, h )
		gii.emitPythonSignal( 'entity.modified', widget )
		mock.markProtoInstanceFieldsOverrided(
			widget, 
			'size'
		)
		if dx ~= 0 or dy ~= 0 then
			mock.markProtoInstanceFieldsOverrided(
				widget, 
				'loc'
			)
		end
	end

	rect:updateShape()
end

--------------------------------------------------------------------
function mock.UIWidget:onBuildManipulator()
	return UIWidgetManipulator()
end

updateAllSubClasses( mock.UIWidget )
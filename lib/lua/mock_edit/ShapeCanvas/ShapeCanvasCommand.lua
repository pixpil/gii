module 'mock_edit'

--------------------------------------------------------------------
CLASS: CmdShapeCanvasBase ( mock_edit.EditorCommand )

function CmdShapeCanvasBase:affirmSelectedCanvas()
	self.targetCanvas = false
	local targetEntity = gii.getSelection( 'scene' )[1]
	if not targetEntity then return false end
	local canvas = self.targetEntity:com( mock.ShapeCanvas )
	if not canvas then return false end
	self.targetCanvas = canvas
	return true
end


--------------------------------------------------------------------
CLASS: CmdShapeCanvasRemove ( CmdShapeCanvasBase )
	:register( 'scene_editor/shape_canvas_remove' )

function CmdShapeCanvasRemove:init( option )
	if not self:affirmSelectedCanvas() then return end
	self.targetItem = option[ 'item' ]
end

function CmdShapeCanvasRemove:redo()
	self.targetCanvas:removeShape( self.targetItem )
end

function CmdShapeCanvasRemove:undo()
	self.targetCanvas:addShape( self.targetItem )
end


--------------------------------------------------------------------
CLASS: CmdShapeCanvasClear ( CmdShapeCanvasBase )
	:register( 'scene_editor/shape_canvas_clear' )

function CmdShapeCanvasClear:init( option )
	if not self:affirmSelectedCanvas() then return end
	self.retainedItems = {}
end

function CmdShapeCanvasClear:redo()
	self.retainedItems = self.targetCanvas.items or {}
	self.targetCanvas:clear()
end

function CmdShapeCanvasClear:undo()
	self.targetCanvas.items = self.retainedItems
end



--------------------------------------------------------------------
CLASS: CmdShapeCanvasAdd ( CmdShapeCanvasBase )
	:register( 'scene_editor/shape_canvas_add' )

function CmdShapeCanvasAdd:init( option )
	if not self:affirmSelectedCanvas() then return end
	self.shapeType = option[ 'type' ]
	self.createdShape = false
end

function CmdShapeCanvasAdd:redo()
	if self.createdShape then
		self.targetCanvas:addShape( self.createdShape )
	else
		local stype = self.shapeType
		if stype == 'point' then
		elseif stype == 'rect' then
		elseif stype == 'circle' then
		elseif stype == 'polygon' then
		end
	end
end

function CmdShapeCanvasAdd:undo()
end

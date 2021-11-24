module 'mock_edit'

-- registerCanvasTool( 'shape_canvas_editor', ShapeCanvasEditor )

-- --------------------------------------------------------------------
-- CLASS: ShapeCanvasTool ( CanvasTool )
-- 	:MODEL{}


-- function ShapeCanvasTool:__init()
-- 	self.currentTarget = false
-- end

-- function ShapeCanvasTool:onLoad()
-- 	ShapeCanvasTool.__super.onLoad( self )
-- 	self:installInput()
-- 	self:updateSelection()
-- end

-- function ShapeCanvasTool:onSelectionChanged( selection )
-- 	self:updateSelection()
-- end

-- function ShapeCanvasTool:updateSelection()
-- 	local selection = self:getSelection()
-- 	if #selection == 1 then --only single selection supported
-- 		local targetEnt = selection[ 1 ]
-- 		local canvas = targetEnt:com( 'ShapeCanvas' )
-- 		self:setTargetCanvas( canvas )
-- 	else
-- 		self:setTargetCanvas( false )
-- 	end
-- end

-- function ShapeCanvasTool:setTargetCanvas( canvas )
-- 	local prevCanvas = self.targetCanvas
-- 	if prevCanvas then
-- 	end
-- 	self.targetCanvas = canvas
-- end

-- function ShapeCanvasTool:createHandle( shape )
-- end

-- registerCanvasTool( 'shape_canvas_tool', ShapeCanvasTool )

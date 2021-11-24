module 'mock_edit'

--------------------------------------------------------------------
---Transform Tool
--------------------------------------------------------------------
CLASS: TransformTool ( SelectionTool )

function TransformTool:__init()
	self.handle = false
end

function TransformTool:onLoad()
	TransformTool.__super.onLoad( self )
	self:installInput()
	self:updateSelection()
end

function TransformTool:onSelectionChanged( selection )
	self:updateSelection()
end

function TransformTool:preCanvasDraw()
	if self.target then
		self.target:updatePivot()
	end
end

function TransformTool:updateSelection()
	local selection = self:getSelection()
	local entities = {}
	for i, e in ipairs( selection ) do
		if isInstance( e, mock.Entity ) then entities[ e ] = true end
	end

	if self.handle then
		self:removeCanvasItem( self.handle )
	end
	self.handle = false
	self.target = false

	local topEntities = self:findTopLevelEntities( entities )
	if topEntities and next( topEntities ) then
		local target = mock_edit.TransformToolHelper()
		target:setTargets( topEntities )
		self.target = target
		self.handle = self:createHandle( target )
		self:addCanvasItem( self.handle )
	end
	self:updateCanvas()
end

function TransformTool:createHandle( target )
	--Abstract
end


--------------------------------------------------------------------
CLASS: TranslationTool ( TransformTool )
	:MODEL{}

function TranslationTool:createHandle( target )
	local handle = TranslationHandle()
	handle:setTarget( target )
	return handle
end

function TranslationTool:onKeyDown( key )
	local action = false
	local inputDevice = self:getInputDevice()

	if self.target then
		local dx, dy, dz = 0,0,0
		if key == 'up' then
			action = 'move'
			dy =  ( inputDevice:isShiftDown() and 10 or 1 )
		elseif key == 'down' then
			action = 'move'
			dy = -( inputDevice:isShiftDown() and 10 or 1 )
		elseif key == 'left' then
			action = 'move'
			dx = -( inputDevice:isShiftDown() and 10 or 1 )
		elseif key == 'right' then
			action = 'move'
			dx =  ( inputDevice:isShiftDown() and 10 or 1 )
		end

		if action == 'move' then
			if inputDevice:isCtrlDown() then
				dz = dy
				dy = 0
			end
			local x, y, z = self.target:getLoc()
			self.target:setLoc( x + dx, y + dy, z + dz )
			self:updateCanvas()
		end

	end	

end

--------------------------------------------------------------------
CLASS: RotationTool ( TransformTool )
	:MODEL{}

function RotationTool:createHandle( target )
	local handle = RotationHandle()
	handle:setTarget( target )
	if target.targetCount > 1 then
		target:setUpdateMasks( true, true, false )
	else
		target:setUpdateMasks( false, true, false )
	end
	return handle
end

--------------------------------------------------------------------
CLASS: ScaleTool ( TransformTool )
	:MODEL{}

function ScaleTool:createHandle( target )
	local handle = ScaleHandle()
	handle:setTarget( target )
	if target.targetCount > 1 then
		target:setUpdateMasks( false, true, true )
	else
		target:setUpdateMasks( false, false, true )
	end
	return handle
end

--------------------------------------------------------------------
registerCanvasTool( 'translation', TranslationTool )
registerCanvasTool( 'rotation',    RotationTool    )
registerCanvasTool( 'scale',       ScaleTool       )

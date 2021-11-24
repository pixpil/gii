module 'mock_edit'

CLASS: CanvasItemVert ( CanvasItem )
	:MODEL{}

function CanvasItemVert:__init()
	self.size  = 5
	self.shape = 'box'
	self.state = 'normal'
end

function CanvasItemVert:setShape( shape )
	self.shape = shape
end

function CanvasItemVert:onLoad()
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
	self:setPivZ( -10 )
end

-- function CanvasItemVert:setItemScl( scl )
-- 	return self.drawScript:setScl( scl, scl, scl )
-- end

function CanvasItemVert:setState( state )
	local state0 = self.state
	if state0 == state then return end
	self.state = state
	return self:onStateChange( state, state0 )
end

function CanvasItemVert:onStateChange( state, state0 )
end

function CanvasItemVert:inside( x, y )
	x, y = self:worldToModel( x, y )
	local padding = 8
	local scl = self.itemScl
	local size = self.size/2 + padding
	return math.abs( x ) <= size and math.abs( y ) <= size
end

function CanvasItemVert:onDraw()
	local size = self.size
	local shape = self.shape
	if shape == 'box' then
		applyColor( 'cp', self.state )
		MOAIDraw.fillRect( -size/2, -size/2, size, size )
		applyColor 'cp-border'
		MOAIDraw.drawRect( -size/2, -size/2, size, size )
	elseif shape == 'circle' then
		applyColor( 'cp', self.state )
		MOAIDraw.fillCircle( 0, 0, size )
		applyColor 'cp-border'
		MOAIDraw.drawCircle( 0, 0, size )
	end
end

function CanvasItemVert:onMouseDown( btn, x, y )
	if btn == 'left' then
		local x0, y0 = self:getLoc()
		self.dragFrom = { x, y, x0, y0 }
		self:onPress()
	end
end

function CanvasItemVert:onDrag( btn, x, y )
	if btn == 'left' then
		local dragFrom = self.dragFrom
		local dx, dy = x - dragFrom[ 1 ], y - dragFrom[ 2 ]
		local x1, y1 = dragFrom[3] + dx, dragFrom[ 4 ] + dy
		x1, y1 = self:snapMove( x1, y1 )
		self:setLoc( x1, y1 )
		self:onMove()
	end
end

function CanvasItemVert:snapMove( x, y )
	return x, y
end

function CanvasItemVert:onMouseUp( btn, x, y )
	-- print( 'mouse up')
end

function CanvasItemVert:onPress()
end

function CanvasItemVert:onMove()
end


module 'mock_edit'


--------------------------------------------------------------------
CLASS: CanvasItemRect ( CanvasItem )

function CanvasItemRect:__init()
	self.size = { 0, 0 }
	self.drawScript = mock.DrawScript()
	self.drawScript:setBlend( 'alpha' )
end

function CanvasItemRect:onLoad()
	self:attach( self.drawScript )
end

function CanvasItemRect:setSize( w, h )
	self.size = { w, h }
	self.drawScript:setBounds( -w/2, -h/2,0, w/2,h/2,0 )
end

function CanvasItemRect:getSize()
	return unpack( self.size )
end

function CanvasItemRect:onDraw()
	applyColor 'shape-line'
	local w, h = self:getSize()
	MOAIDraw.drawRect( -w/2, -h/2, w/2, h/2 )
end


--------------------------------------------------------------------
CLASS: CanvasItemCircle ( CanvasItem )

function CanvasItemCircle:__init()
	self.radius = 0
	self.drawScript = mock.DrawScript()
	self.drawScript:setBlend( 'alpha' )
end

function CanvasItemCircle:onLoad()
	self:attach( self.drawScript )
end

function CanvasItemCircle:setRadius( radius )
	self.radius = radius
	self.drawScript:setBounds( -radius, -radius,0,radius,radius,0 )
end

function CanvasItemCircle:onDraw()
	applyColor 'shape-line'
	MOAIDraw.drawCircle( 0,0, self.radius )
end



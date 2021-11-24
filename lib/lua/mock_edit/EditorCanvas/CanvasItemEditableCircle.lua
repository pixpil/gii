module 'mock_edit'

--------------------------------------------------------------------
CLASS: CanvasItemEditableCircle ( CanvasItem )

function CanvasItemEditableCircle:__init()
	self.radius = 0
end

function CanvasItemEditableCircle:onLoad()
	self.vertC = self:addSubItem( CanvasItemVert() )
	self.vertR = self:addSubItem( CanvasItemVert() )
	linkLoc( self:getProp(), self.vertC:getProp() )

	self.vertC.onMove = function( vert ) return self:onVertMove( 'C' ) end
	self.vertR.onMove = function( vert ) return self:onVertMove( 'R' ) end
	self.vertC:setShape( 'circle' )
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end

function CanvasItemEditableCircle:isConstantSize()
	return false
end

function CanvasItemEditableCircle:onDraw()
	applyColor 'shape-fill'
	MOAIDraw.fillCircle( 0,0, self.radius )
	applyColor 'shape-line'
	MOAIDraw.drawCircle( 0,0, self.radius )
	MOAIDraw.drawLine( 0,0, self.radius, 0 )
end

function CanvasItemEditableCircle:onVertMove( id )
	local vertC = self.vertC
	local vertR = self.vertR
	if id == 'C' then
		local x0, y0 = vertC:getLoc()
		return self:setShape( x0, y0, self.radius, true )
	elseif id == 'R' then
		local x0, y0 = vertC:getLoc()
		local xr = vertR:getLocX()
		local radius = xr - x0
		self.radius = radius
		return self:setShape( x0, y0, radius, true )
	end
end

function CanvasItemEditableCircle:updateShape()
	local x , y, radius = self:onPullAttr()
	if not x then return end
	return self:setShape( x, y, radius, false )
end

function CanvasItemEditableCircle:setShape( x, y, radius, sync )
	self.vertC:setLoc( x, y )
	self.vertR:setLoc( x + radius, y )
	self.radius = radius
	self.drawScript:setBounds( -radius, -radius,0,radius,radius,0 )
	if sync then
		self:onPushAttr( x, y, radius )
	end
end

function CanvasItemEditableCircle:onPullAttr()
	return nil
end

function CanvasItemEditableCircle:onPushAttr( x, y, radius )
end

function CanvasItemEditableCircle:onUpdate()
	self:updateShape()
end
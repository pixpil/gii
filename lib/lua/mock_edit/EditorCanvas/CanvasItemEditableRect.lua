module 'mock_edit'

--------------------------------------------------------------------
CLASS: CanvasItemEditableRect ( CanvasItem )

function CanvasItemEditableRect:__init()
	self.size = { 0, 0 }
	self.rot = 0
	self.filled = true
	self.flipY = false
end

function CanvasItemEditableRect:onLoad()
	self.vertC = self:addSubItem( CanvasItemVert() )
	
	self.vertT = self:addSubItem( CanvasItemVert() )
	self.vertL = self:addSubItem( CanvasItemVert() )
	self.vertR = self:addSubItem( CanvasItemVert() )
	self.vertB = self:addSubItem( CanvasItemVert() )

	self.vertLT = self:addSubItem( CanvasItemVert() )
	self.vertRT = self:addSubItem( CanvasItemVert() )
	self.vertLB = self:addSubItem( CanvasItemVert() )
	self.vertRB = self:addSubItem( CanvasItemVert() )

	self.vertC.onMove = function( vert ) return self:onVertMove( 'C', vert ) end
	self.vertC:setShape( 'circle' )

	self.vertT.onMove = function( vert ) return self:onVertMove( 'T', vert ) end
	self.vertL.onMove = function( vert ) return self:onVertMove( 'L', vert ) end
	self.vertR.onMove = function( vert ) return self:onVertMove( 'R', vert ) end
	self.vertB.onMove = function( vert ) return self:onVertMove( 'B', vert ) end
	self.vertLT.onMove = function( vert ) return self:onVertMove( 'LT', vert ) end
	self.vertRT.onMove = function( vert ) return self:onVertMove( 'RT', vert ) end
	self.vertLB.onMove = function( vert ) return self:onVertMove( 'LB', vert ) end
	self.vertRB.onMove = function( vert ) return self:onVertMove( 'RB', vert ) end

	linkLoc( self:getProp(), self.vertC:getProp() )

	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end

function CanvasItemEditableRect:isConstantSize()
	return false
end

function CanvasItemEditableRect:onDraw()
	local w, h = self:getSize()
	if self.filled then
		applyColor 'shape-fill'
		MOAIDraw.fillRect( -w/2, -h/2, w/2, h/2 )
	end
	applyColor 'shape-line'
	MOAIDraw.drawRect( -w/2, -h/2, w/2, h/2 )
	
end

function CanvasItemEditableRect:getSize()
	return unpack( self.size )
end

function CanvasItemEditableRect:onVertMove( id, vert )
	local vertC = self.vertC
	local inputDevice = self:getView():getInputDevice()
	local altDown = inputDevice:isAltDown()
	if id == 'C' then
		local x0, y0 = vertC:getLoc()
		local w, h = self:getSize()
		local rot  = 0
		return self:setShape( x0, y0, w, h ,0, true )
	else
		local x0, x1 = self.vertL:getLocX() , self.vertR:getLocX()
		local y0, y1 = self.vertB:getLocY() , self.vertT:getLocY()
		local xc0, yc0 = self.vertC:getLoc()
		if id == 'LT' then
			x0 = vert:getLocX()
			y1 = vert:getLocY()
			if altDown then
				x1 = xc0 + ( xc0 - x0 )
				y0 = yc0 + ( yc0 - y1 )
			end
		elseif id == 'RT' then
			x1 = vert:getLocX()
			y1 = vert:getLocY()
			if altDown then
				x0 = xc0 + ( xc0 - x1 )
				y0 = yc0 + ( yc0 - y1 )
			end
		elseif id == 'LB' then
			x0 = vert:getLocX()
			y0 = vert:getLocY()
			if altDown then
				x1 = xc0 + ( xc0 - x0 )
				y1 = yc0 + ( yc0 - y0 )
			end
		elseif id == 'RB' then
			x1 = vert:getLocX()
			y0 = vert:getLocY()
			if altDown then
				x0 = xc0 + ( xc0 - x1 )
				y1 = yc0 + ( yc0 - y0 )
			end
		elseif id == 'L' then
			if altDown then
				x1 = xc0 + ( xc0 - x0 )
			end
		elseif id == 'R' then
			if altDown then
				x0 = xc0 + ( xc0 - x1 )
			end
		elseif id == 'B' then
			if altDown then
				y1 = yc0 + ( yc0 - y0 )
			end
		elseif id == 'T' then
			if altDown then
				y0 = yc0 + ( yc0 - y1 )
			end
		end
		local xc,yc = (x0+x1)/2, (y0+y1)/2
		if x1-x0 < 0 then return end
		if y1-y0 < 0 then return end

		local w, h = math.max( x1 - x0, 0 ), math.max( y1 - y0, 0 )
		return self:setShape( xc, yc, w, h, 0, true )
	end
end

function CanvasItemEditableRect:updateShape()
	local x, y,  w, h, rot = self:onPullAttr()
	if not x then return end
	return self:setShape( x, y, w, h, rot )
end

function CanvasItemEditableRect:setShape( x, y, w, h, rot, sync )
	-- local ent = shape._entity
	self.vertC:setLoc( x +    0, y + 0    )

	self.vertT:setLoc( x +    0, y +  h/2 )
	self.vertB:setLoc( x +    0, y + -h/2 )
	self.vertL:setLoc( x + -w/2, y + 0    )
	self.vertR:setLoc( x +  w/2, y + 0    )

	self.vertLT:setLoc( x + -w/2, y +  h/2 )
	self.vertRT:setLoc( x +  w/2, y +  h/2 )
	self.vertLB:setLoc( x + -w/2, y + -h/2 )
	self.vertRB:setLoc( x +  w/2, y + -h/2 )

	self.drawScript:setBounds( -w/2, -h/2,0, w/2,h/2,0 )
	self.size = { w, h }
	self.rot  = rot
	if sync then
		self:onPushAttr( x, y, w, h, rot or 0 )
	end
end

function CanvasItemEditableRect:onPullAttr()
	return nil
end

function CanvasItemEditableRect:onPushAttr( x, y, w, h, rot )
end

function CanvasItemEditableRect:onUpdate()
	self:updateShape()
end

function CanvasItemEditableRect:inside()
	return false
end
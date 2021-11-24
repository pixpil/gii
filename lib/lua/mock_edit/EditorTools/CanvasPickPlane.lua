module 'mock_edit'

CLASS: CanvasPickPlane ( CanvasItem )
	:MODEL{}

function CanvasPickPlane:__init()
	self.pickingMode = false
	self.pickingFrom = false
	self.x0 = 0
	self.y0 = 0
	self.x1 = 0
	self.y1 = 0
	self.allowRectPicking = true
end

function CanvasPickPlane:onLoad()
	self:attach( mock.DrawScript() ):setBlend( 'alpha' )
end

function CanvasPickPlane:inside()
	return true
end

function CanvasPickPlane:onDraw()
	local x0 = self.x0
	local y0 = self.y0
	local x1 = self.x1
	local y1 = self.y1
	MOAIDraw.setPenColor( 0.4,.5,1,0.2 )
	MOAIDraw.fillRect( x0,y0,x1,y1 )
	MOAIDraw.setPenColor( 0.4,.5,1,1 )
	MOAIDraw.drawRect( x0,y0,x1,y1 )
end

function CanvasPickPlane:onMouseDown( btn, x, y )
	if self.pickingMode then return end
	if self:getInputDevice():isKeyDown( 'space' ) then return end
	if btn == 'left' or btn == 'right' then
		local view = self:getView()
		self.x0 = x
		self.y0 = y
		self.x1 = x 
		self.y1 = y
		self.pickingMode = btn == 'right' and 'selective' or 'normal'
		self:setVisible( true )
		self:getView():updateCanvas()
	end
end

function CanvasPickPlane:onDrag( btn, x, y )
	if not self.pickingMode then return end
	if not self.allowRectPicking then return end
	local view = self:getView()
	self.x1 = x
	self.y1 = y
	self:getView():updateCanvas()
end

function CanvasPickPlane:onMouseUp( btn )
	if not self.pickingMode then return end
	local pickingMode = self.pickingMode
	self.pickingMode = false
	self:setVisible( false )
	self:getView():updateCanvas()
	
	local ignoreEditLock = self:getInputDevice():isKeyDown( 'lmeta' )

	local x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
	local dx, dy = x1-x0, y1-y0
	if (dx*dx+dy*dy) < 5 then --Point pick
		local picked = self:getView():pick( x1, y1, nil, pickingMode == 'selective', ignoreEditLock )
		if self.onPicked then
			return self.onPicked( picked, pickingMode )
		end
	else
		local picked = self:getView():pickRect( x0, y0, x1, y1, nil, pickingMode == 'selective', ignoreEditLock )
		if self.onPicked then
			return self.onPicked( picked, pickingMode )
		end
	end
		
end

function CanvasPickPlane:setPickCallback( cb )
	self.onPicked = cb
end

function CanvasPickPlane:isConstantSize()
	return false
end

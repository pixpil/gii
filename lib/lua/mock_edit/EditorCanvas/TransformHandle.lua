module 'mock_edit'
--------------------------------------------------------------------
local handleSize = 80
local handleArrowSize = 12
local handlePad = 20
--------------------------------------------------------------------
---Handles
--------------------------------------------------------------------
CLASS: TranslationHandle( CanvasItem )
function TranslationHandle:__init( option )
	self.option = option
	self.activeAxis = false
end

function TranslationHandle:onLoad()
	local option = self.option
	self:attach( mock.DrawScript() )	
end

function TranslationHandle:onDraw()	
	applyColor 'handle-z'
	MOAIDraw.drawRect( 0,0, handleArrowSize, handleArrowSize )
	--x axis
	applyColor 'handle-x'
	MOAIDraw.drawLine( 0,0, handleSize, 0 )
	MOAIDraw.fillFan(
		handleSize,  handleArrowSize/3, 
		handleSize + handleArrowSize, 0,
		handleSize, -handleArrowSize/3
		-- handleSize,  handleArrowSize/3
		)
	-- MOAIDraw.fillFan( 0,0, handleSize / 5, handleSize / 5 )
	--y axis
	applyColor 'handle-y'
	MOAIDraw.drawLine( 0,0, 0, handleSize )
	MOAIDraw.fillFan(
		handleArrowSize/3, handleSize, 
		0, handleSize + handleArrowSize,
		-handleArrowSize/3, handleSize 
		-- handleArrowSize/3, handleSize, 
		)
end

-- function TranslationHandle:wndToTarget( x, y )
-- 	local x, y = self:wndToWorld( x, y )
-- 	if self.target then 
-- 		local parent = self.target.parent
-- 		if parent then
-- 			return parent:worldToModel( x, y )
-- 		end
-- 	end
-- 	return x, y
-- end

function TranslationHandle:setTarget( target )
	self.target = target
	target:setUpdateMasks( true, false, false )
	inheritLoc( self:getProp(), target:getProp() )
end

function TranslationHandle:inside( x, y )
	return self:calcActiveAxis( x, y ) ~= false
end

function TranslationHandle:calcActiveAxis( x, y )
	x, y = self:worldToModel( x, y )
	if x >= 0 and y >= 0 and x <= handleArrowSize + handlePad and y <= handleArrowSize + handlePad then
		return 'all'
	elseif math.abs( y ) < handlePad and x <= handleSize + handleArrowSize and x > -handlePad then
		return 'x'
	elseif math.abs( x ) < handlePad and y <= handleSize + handleArrowSize and y > -handlePad then
		return 'y'
	end
	return false
end

function TranslationHandle:onMouseDown( btn, x, y )
	if btn~='left' then return end
	self.activeAxis = false
	self.x0, self.y0 = x, y

	target = self.target
	local tx, ty, tz = self.target:getLoc()
	self.tx0, self.ty0, self.tz0 = tx, ty, tz

	self.activeAxis = self:calcActiveAxis( x, y )
	if self.activeAxis then
		self.target:preTransform()
		return true
	end
end

function TranslationHandle:onMouseUp( btn, x, y )
	if btn~='left' then return end
	if not self.activeAxis then return end
	self.activeAxis = false
	return true
end

function TranslationHandle:onDrag( btn, x, y )
	if not self.activeAxis then return end
	local target = self.target
	target:forceUpdate()
	self:forceUpdate()
	local dx = x - self.x0
	local dy = y - self.y0

	local tx0, ty0, tz0 = self.tx0, self.ty0, self.tz0
	local tx, ty, tz = tx0 + dx, ty0, tz0
	
	-- local mode = 'global'
	-- local parent = target.parent
	-- if parent and mode == 'global' then
	-- 	local wx, wy   = target:getWorldLoc()
	-- 	local wx1, wy1 = parent:modelToWorld( tx + dx, ty + dy )
	-- 	wx1, wy1 = self:getView():snapLoc( wx1, wy1 )
	-- 	if self.activeAxis == 'all' then
	-- 		--pass			
	-- 	elseif self.activeAxis == 'x' then
	-- 		wy1 = wy
	-- 	elseif self.activeAxis == 'y' then
	-- 		wx1 = wx
	-- 	end
	-- 	tx, ty = parent:worldToModel( wx1, wy1 )
	-- else
	-- 	local wx1, wy1 = tx + dx, ty + dy
	-- 	wx1, wy1 = self:getView():snapLoc( wx1, wy1 )
	-- 	if self.activeAxis == 'all' then
	-- 		--pass
	-- 	elseif self.activeAxis == 'x' then
	-- 		wy1 = ty
	-- 	elseif self.activeAxis == 'y' then
	-- 		wx1 = tx
	-- 	end
	-- 	tx, ty = wx1, wy1
	-- end
	if self:getInputDevice():isCtrlDown() then
		tz = tz + dy
	else
		ty = ty + dy
	end

	tx, ty = self:getView():snapLoc( tx, ty, nil, self.activeAxis )
	if self.activeAxis == 'all' then
		--pass
	elseif self.activeAxis == 'x' then
		ty = ty0
		tz = tz0
	elseif self.activeAxis == 'y' then
		tx = tx0
	end
	target:setLoc( tx, ty, tz )
	-- self.tool:updateCanvas()
	return true
end


--------------------------------------------------------------------
---ROTATION
--------------------------------------------------------------------

CLASS: RotationHandle( CanvasItem )
function RotationHandle:__init( option )
	self.option = option
	self.align  = false
	self.active = false
	self.size   = handleSize
end

function RotationHandle:onLoad()
	self:attach( mock.DrawScript() )
end

function RotationHandle:setTarget( target )
	self.target = target
	inheritLoc( self:getProp(), target:getProp() )
	self.r0 = target:getRotZ()
end

function RotationHandle:inside( x, y )
	local x1, y1 = self:worldToModel( x, y )
	local r = distance( 0,0, x1,y1 )
	return r <= self.size
end

function RotationHandle:onDraw()
	if self.active then
		applyColor 'handle-active'
	else
		applyColor 'handle-z'
	end
	MOAIDraw.fillCircle( 0, 0, 5 )
	MOAIDraw.drawCircle( 0, 0, self.size )
	local r = self.target:getRotZ()	
	MOAIDraw.drawLine( 0,0, vecAngle( r, self.size ) )
	if self.active then
		applyColor 'handle-previous'
		MOAIDraw.drawLine( 0,0, vecAngle( self.r0, self.size ) )
	end
end

function RotationHandle:onMouseDown( btn, x, y )
	if btn~='left' then return end
	
	local x1, y1 = self:worldToModel( x, y )
	local rx,ry,rz = self.target:getRot()
	self.rot0 = rz
	self.dir0 = direction( 0,0, x1,y1 )
	self.active = true

	self.target:preTransform()	
	self.r0 = self.target:getRotZ()
	-- self.tool:updateCanvas()
	return true
end

function RotationHandle:onDrag( btn, x, y )
	if not self.active then return end
	local x1, y1 = self:worldToModel( x, y )
	local r = distance( 0,0, x1,y1 )
	if r>5 then
		local dir = direction( 0,0, x1,y1)
		local ddir = dir - self.dir0
		local rx,ry,rz = self.target:getRot()
		rz = self.rot0 + ddir * 180/math.pi
		self.target:setRot( rx, ry, rz )
		gii.emitPythonSignal( 'entity.modified', self.target, 'view' )
		-- self.tool:updateCanvas()
	end
	return true
end

function RotationHandle:onMouseUp( btn, x, y )
	if btn~='left' then return end
	if not self.active then return end
	self.active = false
	-- self.tool:updateCanvas()
	return true
end

--------------------------------------------------------------------
---SCALE Handle
--------------------------------------------------------------------
CLASS: ScaleHandle( CanvasItem )
function ScaleHandle:__init( option )
	self.option = option
	self.activeAxis = false
end

function ScaleHandle:onLoad()
	local option = self.option
	self:attach( mock.DrawScript() )	
end

function ScaleHandle:onDraw()
	applyColor 'handle-z'
	MOAIDraw.fillRect( 0, 0, handleArrowSize, handleArrowSize )
	--x axis
	applyColor 'handle-x'
	MOAIDraw.drawLine( 0, 0, handleSize, 0 )
	MOAIDraw.fillRect( handleSize,0, handleSize + handleArrowSize, handleArrowSize )
	--y axis
	applyColor 'handle-y'
	MOAIDraw.drawLine( 0, 0, 0, handleSize )
	MOAIDraw.fillRect( 0, handleSize, handleArrowSize, handleSize + handleArrowSize )
end

function ScaleHandle:setTarget( target )
	self.target = target
	inheritLoc( self:getProp(), target:getProp() )
end


function ScaleHandle:inside( x, y )
	return self:calcActiveAxis( x, y ) ~= false
end

function ScaleHandle:calcActiveAxis( x, y )
	x, y = self:worldToModel( x, y )
	if x >= 0 and y >= 0 and x <= handleArrowSize + handlePad and y <= handleArrowSize + handlePad then
		return 'all'
	elseif math.abs( y ) < handlePad and x <= handleSize + handleArrowSize and x > -handlePad then
		return 'x'
	elseif math.abs( x ) < handlePad and y <= handleSize + handleArrowSize and y > -handlePad then
		return 'y'
	end
	return false
end

function ScaleHandle:onMouseDown( btn, x, y )
	if btn~='left' then return end	
	self.x0 = x
	self.y0 = y
	self.activeAxis = self:calcActiveAxis( x, y )
	self.sx, self.sy, self.sz = self.target:getScl()
	if self.activeAxis then
		self.target:preTransform()
		return true
	end

end

function ScaleHandle:onMouseUp( btn, x, y )
	if btn~='left' then return end
	if not self.activeAxis then return end
	self.activeAxis = false
	return true
end

function ScaleHandle:onDrag( btn, x, y )
	if not self.activeAxis then return end
	local target = self.target
	target:forceUpdate()
	self:forceUpdate()
	
	local dx = x - self.x0
	local dy = y - self.y0

	local mode = 'global'
	local parent = target.parent
	-- if parent and mode == 'global' then
		if self.activeAxis == 'all' then
			local k = 1 + math.magnitude( dx, dy ) / 100 * math.sign(dx) 
			self.target:setScl( 
				self.sx * k,
				self.sy * k,
				self.sz * 1 )
		elseif self.activeAxis == 'x' then
			local k = 1 + math.magnitude( dx, 0 ) / 100 * math.sign(dx) 
			self.target:setScl( 
				self.sx * k,
				self.sy * 1,
				self.sz * 1 )

		elseif self.activeAxis == 'y' then
			local k = 1 - math.magnitude( dy, 0 ) / 100 * math.sign(dy) 
			self.target:setScl( 
				self.sx * 1,
				self.sy * k,
				self.sz * 1 )
		end
		
	-- else
	-- 	local k = 1 + math.magnitude( dx, dy ) / 100 * math.sign(dx) 
	-- 	self.target:setScl( 
	-- 		self.sx * k,
	-- 		self.sy * k,
	-- 		self.sz * 1 )
	-- end
	
	-- self.tool:updateCanvas()
	return true
end

module 'mock_edit'

--------------------------------------------------------------------
--CanvasNavigate
--------------------------------------------------------------------
CLASS: CanvasNavigate( EditorEntity )

function CanvasNavigate:__init( option )
	self.option = option
	self.accumulatedScrollY = 0
end

function CanvasNavigate:onLoad()
	local option = self.option or {}
	local inputDevice = option.inputDevice or self:getScene():getEditorInputDevice()
	self.targetCamera = assert( option.camera or self:getScene().camera )
	self:attach( mock.InputScript{ 
			device = inputDevice
		} )
	self.inputDevice = inputDevice
	self.zoom = 1
	self.dragging = false
	self.onZoomChanged = option.onZoomChanged or false
	self.onLocChanged = option.onLocChanged or false
end

function CanvasNavigate:reset()
	self.targetCamera:setLoc( 0,0,0 )
	self.targetCamera:setRot( 0,0,0 )
	self.targetCamera:setScl( 1,1,1 )
	self.targetCamera:com():setZoom( 1 )
end


function CanvasNavigate:startDrag( btn, x, y )
	self.dragFrom = { x, y }
	self.cameraFrom = { self.targetCamera:getLoc() }
	self.dragging = btn
	self.targetCamera:com():setCursor( 'closed-hand' )
end

function CanvasNavigate:stopDrag()
	self.dragging = false
	self.targetCamera:com():setCursor( 'arrow' )
end

function CanvasNavigate:onMouseDown( btn, x, y )
	if btn == 'middle' then
		if self.dragging then return end
		self:startDrag( btn, x, y )

	elseif btn == 'left' then
		if self.dragging then return end
		if self.inputDevice:isKeyDown( 'space' ) then
			self:startDrag( btn, x, y )
		end
		
	end
end

function CanvasNavigate:onMouseUp( btn, x, y )
	if btn == self.dragging then self:stopDrag() end
end

function CanvasNavigate:onMouseMove( x, y )
	if not self.dragging then return end	
	local x0, y0 = unpack( self.dragFrom )
	local dx, dy = x - x0, y - y0
	local cx0, cy0 = unpack( self.cameraFrom )
	local cameraCom = self.targetCamera:getComponent( EditorCanvasCamera )
	local zoom = cameraCom:getZoom()
	local z0 = self.targetCamera:getLocZ()
	local x, y, z = cx0 - dx/zoom, cy0 + dy/zoom, z0
	return self:setCameraLoc( x,y,z )
	-- self.targetCamera:setLoc( x, y, z )
	-- if self.onLocChanged then
	-- 	self.onLocChanged( x, y, z )
	-- end
end

local function getZoomInc( z )
	if z >= 3 then return 1 end
	if z >= 1 then return 0.5 end
	if z >= 0.5 then return 0.25 end
	if z >= 0.25 then return 0.125 end
	if z >= 0.1 then return 0.05 end
	if z >= 0.01 then return 0.01 end
	if z >= 0.0 then return 0.001 end
end

local function getZoomDec( z )
	if z <= 0.01 then return  0.001 end
	if z <= 0.1 then return  0.01 end
	if z <= 0.25 then return  0.05 end
	if z <= 0.5 then return  0.125 end
	if z <= 1 then return  0.25 end
	if z <= 3 then return  0.5 end
	return 1
end

function CanvasNavigate:onMouseScroll( x, y )
	if self.dragging then return end
	if math.sign( y ) ~= math.sign( self.accumulatedScrollY ) then
		self.accumulatedScrollY = 0
	end
	self.accumulatedScrollY = self.accumulatedScrollY + y
	if self.accumulatedScrollY >= 2 then
		local inc = getZoomInc( self.zoom )
		self:setZoom( self.zoom + inc )
		self.accumulatedScrollY = 0
	elseif self.accumulatedScrollY <= -2 then
		local dec = getZoomDec( self.zoom )
		self:setZoom( self.zoom - dec )
		self.accumulatedScrollY = 0
	end
end

function CanvasNavigate:setZoom( zoom )
	zoom = clamp( zoom, 1 / 100, 100 )
	self.zoom = zoom
	local cameraCom = self.targetCamera:getComponent( EditorCanvasCamera )
	cameraCom:setZoom( zoom )
	if self.onZoomChanged then
		self.onZoomChanged( zoom )
	end
	-- MOAINodeMgr.update()
	self:updateCanvas()
end

function CanvasNavigate:updateCanvas()
	local cameraCom = self.targetCamera:getComponent( EditorCanvasCamera )
	cameraCom:updateCanvas()
end


function CanvasNavigate:getCameraLoc()
	return self.targetCamera:getLoc()
end

function CanvasNavigate:setCameraLoc( x,y,z )
	self.targetCamera:setLoc( x,y,z )
	self:updateCanvas()
end


function CanvasNavigate:getCameraZoom()
	return self.zoom
end

function CanvasNavigate:setCameraZoom( z )
	return self:setZoom( z )
end
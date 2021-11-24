module 'mock_edit'

--------------------------------------------------------------------
CLASS: CanvasHandleLayer ( EditorEntity )
function CanvasHandleLayer:__init( option )
	self.option = option
	self.activeHandle = false
	self.handles = {}
	self.pendingNewHandles = {}
	self.iterating = false
end


function CanvasHandleLayer:startIterate()
	self.iterating = true
end

function CanvasHandleLayer:stopIterate()
	self.iterating = false
	self:flushPendingNewHandles()
end

function CanvasHandleLayer:onLoad()
	local option = self.option or {}
	local inputDevice = option.inputDevice or self:getScene():getEditorInputDevice()
	self.targetCamera = assert( option.camera or self:getScene().camera )
	self.targetCameraCom = self.targetCamera:com('EditorCanvasCamera')
	self:attach( mock.InputScript{ 
			device = inputDevice
		} )
	self.targetCameraCom.onZoomChanged = function( zoom )
		return self:onZoomChanged( zoom )
	end
end


function CanvasHandleLayer:onMouseDown( btn, x, y )
	self:startIterate()
	for i, handle in ipairs( self.handles ) do
		if handle:onMouseDown( btn, x, y ) == true then --grabbed
			break
		end
	end
	self:stopIterate()
end

function CanvasHandleLayer:onMouseUp( btn, x, y )
	self:startIterate()
	for i, handle in ipairs( self.handles ) do
		if handle:onMouseUp( btn, x, y ) == true then
			break
		end
	end
	self:stopIterate()
end

function CanvasHandleLayer:onMouseMove( x, y )
	self:startIterate()
	for i, handle in ipairs( self.handles ) do
		if handle:onMouseMove( x, y ) == true then
			break
		end
	end
	self:stopIterate()
end

function CanvasHandleLayer:onZoomChanged( zoom )
	self:startIterate()
	local scl = 1/zoom
	for i, handle in ipairs( self.handles ) do
		handle:setScl( scl, scl, 1 )
	end
	self:stopIterate()
end

function CanvasHandleLayer:addHandle( handle )
	local scene = self:getScene()
	scene:addEntity( handle )
	handle.handleLayer = self
	local scl = 1/self.targetCameraCom:getZoom()
	handle:setScl( scl, scl, 1 )
	handle:setPriority( 1000 )
	handle:setLoc( 0,0,self:getLocZ())
	if self.iterating then
		table.insert( self.pendingNewHandles, handle )
	else
		table.insert(self.handles, 1, handle )
	end
	return handle
end

function CanvasHandleLayer:flushPendingNewHandles()
	for i, handle in ipairs( self.pendingNewHandles ) do
		table.insert( self.handles, 1, handle )
	end
	self.pendingNewHandles = {}
end

function CanvasHandleLayer:updateCanvas( ... )
	if self._onUpdate then
		return self._onUpdate( ... )
	end
end

function CanvasHandleLayer:setUpdateCallback( update )
	self._onUpdate = update
end

function CanvasHandleLayer:clearHandles()
	for i,h in ipairs( self.handles ) do	
		h:destroyWithChildrenNow()
	end
end


--------------------------------------------------------------------
CLASS: CanvasHandle ( EditorEntity )

function CanvasHandle:onMouseDown( btn, x, y )
end

function CanvasHandle:onMouseUp( btn, x, y )
end

function CanvasHandle:onMouseMove( x, y )
end

function CanvasHandle:updateCanvas()
	self.handleLayer:updateCanvas()
end

function CanvasHandle:onDestroy()
	local handleLayer = self.handleLayer
	if not handleLayer then return end
	for i, h in ipairs( handleLayer.handles ) do
		if h == self then
			return table.remove( self.handleLayer.handles, i )
		end
	end
end


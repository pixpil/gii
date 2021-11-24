module 'mock_edit'
--------------------------------------------------------------------
--EditorCanvasCamera
--------------------------------------------------------------------
CLASS: EditorCanvasCamera ( mock.Camera )
function EditorCanvasCamera:__init( env )
	self.FLAG_EDITOR_OBJECT = true
	self.env = env
	self.parallaxEnabled = false
	self.clearBuffer = true

end

function EditorCanvasCamera:detectRenderContext()
	local giiRenderContext = assert( self.env.getRenderContext(), 'no gii render context' )
	return assert( giiRenderContext:getMockRenderContext(), 'no mock render context:' .. tostring( giiRenderContext ) )
end

function EditorCanvasCamera:loadPasses()
	self:addPass( mock.SceneCameraPass( self.clearBuffer, self.clearColor ) )
end

function EditorCanvasCamera:isEditorCamera()
	return true
end

-- function EditorCanvasCamera:getDefaultOutputRenderTarget()
-- 	return self._renderContext
-- 	context = gii.getCurrentRenderContext()
-- 	local w, h = context.w, context.h
-- 	self.canvasRenderTarget = mock.DeviceRenderTarget( 
-- 		MOAIGfxMgr.getFrameBuffer(), 1, 1
-- 	)
-- 	self:setScreenSize( w or 100, h or 100 )
-- 	return self.canvasRenderTarget
-- end

function EditorCanvasCamera:tryBindSceneLayer( layer )
	local name = layer.name
	if name == '_GII_EDITOR_LAYER' then
		layer:setViewport( self:getMoaiViewport() )
		layer:setCamera( self._camera )
	end
end

-- function EditorCanvasCamera:getScreenRect()
-- 	return self.canvasRenderTarget:getAbsPixelRect()
-- end

-- function EditorCanvasCamera:getScreenScale()
-- 	return self.canvasRenderTarget:getScale()
-- end

-- function EditorCanvasCamera:setScreenSize( w, h )b
-- 	self.canvasRenderTarget:setPixelSize( w, h )
-- 	self.canvasRenderTarget:setFixedScale( w, h )
-- 	self:updateZoom()
-- end

function EditorCanvasCamera:updateCanvas()
	if self.env then 
		self.env.updateCanvas()
	end
end

function EditorCanvasCamera:hideCursor()
	if self.env then self.env.hideCursor() end
end

function EditorCanvasCamera:showCursor()
	if self.env then self.env.showCursor() end
end

function EditorCanvasCamera:setCursor( id )
	if self.env then self.env.setCursor( id ) end
end

function EditorCanvasCamera:onAttach( entity )
	entity.FLAG_EDITOR_OBJECT = true
	return EditorCanvasCamera.__super.onAttach( self, entity)
end


module 'mock_edit'

--------------------------------------------------------------------
CLASS: EditorCanvasContext ( mock.RenderContext )

function EditorCanvasContext:__init( giiContext )
	local mainRenderTarget   = mock.RenderTarget()
	mainRenderTarget:setFrameBuffer( giiContext:getFrameBuffer() )

	mainRenderTarget:setMode( 'fixed' )
	mainRenderTarget:setPixelSize( 1, 1 )
	mainRenderTarget:setScalePerPixel( 1, 1 )

	self:setRenderTarget( mainRenderTarget )
	-- --lift
	-- self.getRenderTargetTexture = self.getRenderTargetTexture
	self.name = giiContext:getName()
end

function EditorCanvasContext:onResize( w, h, scale )
	self.renderTarget:setPixelSize( w * scale, h * scale )
	self.renderTarget:setScalePerPixel( 1/scale )
end

function EditorCanvasContext:getRenderTargetTexture()
	local fb = self.frameBuffer
	if fb then
		return GIIHelper.getGLTexture( fb )
	end
	return 0
end

local _draw = GIIHelper.draw
function EditorCanvasContext:draw()
	return _draw( self.rootRenderPass )
end

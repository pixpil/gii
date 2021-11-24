module 'mock_edit'

--------------------------------------------------------------------
gii.CLASS: GIIMockCanvasContext( gii.GIIRenderContext )

function GIIMockCanvasContext:__init()
	self.mockContext = false
end


function GIIMockCanvasContext:setName( n )
	GIIMockCanvasContext.__super.setName( self, n )
	if self.mockContext then
		self.mockContext:setName( n )
	end
end


function GIIMockCanvasContext:onResize( w, h, scale )
	self.mockContext:setSize( w, h, scale )
end

function GIIMockCanvasContext:onActivate()
	self.mockContext:makeCurrent()
	GIIMockCanvasContext.__super.onActivate( self )
end

function GIIMockCanvasContext:onDeactivate()
	--TODO: reset to game render context
	GIIMockCanvasContext.__super.onDeactivate( self )
end

function GIIMockCanvasContext:getMockRenderContext()
	return self.mockContext
end

function GIIMockCanvasContext:detect()
	GIIMockCanvasContext.__super.detect( self )
	self.mockContext = EditorCanvasContext( self )
	self.mockContext:setName( self:getName() )
	-- self:setRenderTable{
	-- 	self.mockContext:getRenderRoot()
	-- }
end

function GIIMockCanvasContext:onDraw()
	return self.mockContext:draw()
end

--------------------------------------------------------------------
gii.CLASS: GIIMockPreviewCanvasContext( GIIMockCanvasContext )

function GIIMockPreviewCanvasContext:detect()
	GIIMockCanvasContext.__super.detect( self )
	self.mockContext = mock.game:getMainRenderContext()
end

local _draw = GIIHelper.draw
function GIIMockPreviewCanvasContext:draw()
	return _draw( self.mockContext.rootRenderPass )
end

--------------------------------------------------------------------
gii.CLASS: GIIMockDummyCanvasContext( GIIMockCanvasContext )

function GIIMockDummyCanvasContext:__init()
	self.mockContext = mock.DummyRenderContext()
end

function GIIMockDummyCanvasContext:detect()
end


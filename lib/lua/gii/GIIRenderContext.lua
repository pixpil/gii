module 'gii'


--------------------------------------------------------------------
local renderContextManager
function getRenderContextManager()
	return renderContextManager
end

function addContextChangeListeners( f )
	return renderContextManager:addChangeListener( f )
end

function removeContextChangeListener( f )
	return renderContextManager:removeContextChangeListener( f )
end

function getCurrentRenderContext()
	return renderContextManager.currentContext
end

---------------------------------------------------------------------
CLASS: GIIRenderContextManager ()

function GIIRenderContextManager:__init()
	self.contextChangeListeners = {}
	self.contexts = {}
	self.contextMap = {}
	self.currentContext = false
end

function GIIRenderContextManager:addChangeListener( f )
	self.contextChangeListeners[ f ] = true
end

function GIIRenderContextManager:removeChangeListener( f )
	self.contextChangeListeners[ f ] = nil
end

function GIIRenderContextManager:register( context )
	self.contexts[ context ] = true
end

function GIIRenderContextManager:updateMap()
	local map = {}
	for ctx in pairs( self.contexts ) do
		local name = ctx:getName()
		if name then
			map[ name ] = ctx
		end
	end
	self.contextMap = map
end

function GIIRenderContextManager:getContext( name )
	return self.contextMap[ name ]
end

function GIIRenderContextManager:setCurrentContext( context )
	local context0 = self.currentContext
	if context0 == context then return end

	if context0 then
		context0.current = false
		context0:onDeactivate()
	end
	self.currentContext = context
	if context then
		context.current = true
		context:onActivate()
	end
	
	for listener in pairs( self.contextChangeListeners ) do
		listener( context, context0 )
	end

end

function GIIRenderContextManager:draw()
	local context = self.currentContext
	if not context then return false end
	return context:onDraw()
end


--------------------------------------------------------------------
gii.CLASS: GIIRenderContext ()

function GIIRenderContext:__init( name )
	renderContextManager:register( self )
	self.name = name
	self.deviceFrameBuffer = MOAIFrameBuffer.new()
	self.width = false
	self.height = false
	self.clearColor = false

	self.actionRoot     = MOAIAction.new()
	self.actionRoot:setAutoStop( false )
	
	self.clearColorNode = MOAIColor.new()
	self.renderRoot     = MOAITableLayer.new()
	self.hasClearColor  = false

	self.renderRoot:setFrameBuffer( self.deviceFrameBuffer )

	self.contextReady = false

	self.current = false
end

function GIIRenderContext:setName( n )
	self.name = n
	renderContextManager:updateMap()
end

function GIIRenderContext:getName()
	return self.name
end

function GIIRenderContext:makeCurrent()
	renderContextManager:setCurrentContext( self )
end

function GIIRenderContext:getFrameBuffer()
	return self.deviceFrameBuffer
end

function GIIRenderContext:getRenderRoot()
	return self.renderRoot
end

function GIIRenderContext:setRenderTable( t )
	return self.renderRoot:setRenderTable( t )
end

function GIIRenderContext:detect()
	GIIHelper.detectCurrentFrameBuffer( self.deviceFrameBuffer )	
	self.contextReady = true
end

function GIIRenderContext:setClearColor( r,g,b,a )
	if not r then
		self.hasClearColor = false
	else
		self.hasClearColor = true
		self.clearColorNode:setColor( r,g,b,a )
	end
end

function GIIRenderContext:setSize( w, h, scale )
	self.width = w or self.width
	self.height = h or self.height
	self.scale = scale or self.scale

	GIIHelper.resizeFrameBuffer(
		self.deviceFrameBuffer, self.width * scale, self.height * scale, 1
	)
	self:onResize( w, h, scale )
end

function GIIRenderContext:getSize()
	return self.width, self.height
end

function GIIRenderContext:getScale()
	return self.scale
end

function GIIRenderContext:getActionRoot()
	return self.actionRoot
end

--------------------------------------------------------------------
function GIIRenderContext:onResize( w, h, scale )
end

function GIIRenderContext:onActivate()
	MOAIActionMgr.setRoot( self.actionRoot )
end

function GIIRenderContext:onDeactivate()
	-- body	
end

local _draw = GIIHelper.draw
function GIIRenderContext:onDraw()
	return _draw( self.renderRoot )
end

function GIIRenderContext:draw()
	GIIHelper.frameBufferNeedsClear( self.deviceFrameBuffer, true )
	return self:onDraw()
end

--------------------------------------------------------------------


--------------------------------------------------------------------
renderContextManager = GIIRenderContextManager()

module('gii')

---deprectaed

local defaultFont  = false
local defaultStyle = false
		
local function initDefaultStyle()
	defaultFont = MOAIFont.new()
	defaultFont:load( app:findDataFile('default_font.ttf') )
	defaultStyle = MOAITextStyle.new()
	defaultStyle:setFont( defaultFont )
	defaultStyle:setSize( 11 )
end

function getDefaultFont()
	if not defaultStyle then
		initDefaultStyle()
	end
	return defaultFont
end

function getDefaultStyle()
	if not defaultStyle then
		initDefaultStyle()
	end
	return defaultStyle
end

local function makeBackgroundProp( )
	local bgProp = MOAIGraphicsProp.new()
	local bgDeck = MOAIDrawDeck.new()
	local color = {.1,.1,.1,1}
	local size  = {0,0}
	bgDeck:setRect(0,0,1,1)
	bgDeck:setDrawCallback(function()
		local w,h =size[1],size[2]
		MOAIDraw.setPenColor(unpack(color))
		MOAIDraw.fillRect(-w/2,h/2,w/2,-h/2)
	end
	)
	bgProp:setDeck(bgDeck)
	bgProp:setPriority(-10000)
	bgProp._color = color
	bgProp._size  = size
	return bgProp
end


---------Common Context Helper
CLASS: EditCanvasContext ()

function EditCanvasContext:__init()
	local layer = MOAILayer.new ()
	local camera=MOAICamera2D.new()
	local viewport = MOAIViewport.new ()

	MOAISim.pushRenderPass ( layer )
	layer:setViewport ( viewport )
	layer:showDebugLines( false )
	layer:setCamera(camera)

	local bgColor = {.1,.1,.1,1}
	bgProp = makeBackgroundProp( 
		bgColor, layer, camera 
		)
	bgProp:setPartition( layer )
	bgProp:setParent(camera)

	self.layer      = layer
	self.camera     = camera
	self.cameraScl  = 1
	self.viewport   = viewport
	self.background = bgProp
	self.viewWidth  = 0
	self.viewHeight = 0
	self.hudProps   = {}
end

function EditCanvasContext:setRenderContext( context )
	self.renderContext = context
end

function EditCanvasContext:getSize()
	return self.viewWidth, self.viewHeight
end

function EditCanvasContext:resize( w, h )
	self.viewport:setSize(w,h)
	self.viewport:setScale(w,h)

	self.viewWidth, self.viewHeight = w, h

	local size = self.background._size
	size[1]=w
	size[2]=h

	for hud in pairs(self.hudProps) do
		hud:setRect(-w/2 ,-h/2, w/2, h/2)
	end
end

function EditCanvasContext:setBackgroundColor(r,g,b,a)
	local bgColor = self.background._color
	bgColor[1] = r 
	bgColor[2] = g 
	bgColor[3] = b 
	bgColor[4] = a 
end

function EditCanvasContext:insertProp( p )
	return p:setPartition( self.layer )
end

function EditCanvasContext:removeProp( p )
	return p:setPartition( nil )
end

function EditCanvasContext:setCameraScl( scl )
	self.camera:setScl(scl,scl,1)
	self.cameraScl=scl
end
function EditCanvasContext:setCameraLoc( x, y )
	self.camera:setLoc( x, y )
end

function EditCanvasContext:wndToWorld( x, y )
	return self.layer:wndToWorld( x, y )
end

function EditCanvasContext:worldToWnd( x, y, z )
	return self.layer:worldToWnd( x, y, z )
end

function EditCanvasContext:fitViewport( w,h )
	local scl=1
	local vw,vh = self.viewWidth, self.viewHeight
	if w * h<=0 then return end
	if vw*vh<=0 then return end
	scl = math.max(h/vh, w/vw)
	self:setCameraScl(scl)
end

--------------------------------------------------------------------
function createEditCanvasContext()
	return EditCanvasContext()
end

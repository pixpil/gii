--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
scn:init()
scn:start()
--------------------------------------------------------------------

mock_edit.addColor( 'paintcanvas_grid', hexcolor( '#007fff', 0.3 ) )

local shaderScriptBrightness = SHADER_SCRIPT [=[
	shader 'main' {
			uniform = {
				sampler  = sampler( 1 );
			};

			program_vertex = 'vsh';
			program_fragment = 'fsh';
	}


	source 'vsh' [[
		in vec4 position;
		in vec2 uv;
		in vec4 color;

		out LOWP vec4 colorVarying;
		out MEDP vec2 uvVarying;

		void main () {
			gl_Position = position;
			uvVarying = uv;
			colorVarying = color;
		}
	]]

	source 'fsh' [[	
		in LOWP vec4 colorVarying;
		in MEDP vec2 uvVarying;

		@sampler sampler;

		out vec4 FragColor;

		void main () {
			float a = texture ( sampler, uvVarying ).a;
			FragColor.rgb = colorVarying.rgb * a ;
			FragColor.a = colorVarying.a * texture ( sampler, uvVarying ).a;
		}
	]]

]=]


local maskShader = shaderScriptBrightness:affirmDefaultShader():getMoaiShader()


local testImage = gii.findDataFile( 'PaintCanvas/brush/NoiseRadialCircle.png' )
-- local testImage = gii.findDataFile( 'PaintCanvas/brush/SmoothRec.png' )
local testTex = MOAITexture.new()
testTex:load( testImage, MOAIImage.TRUECOLOR )
local testDeck = MOAISpriteDeck2D.new()
testDeck:setTexture( testTex )
testDeck:setShader( maskShader )
testDeck:setRect( -0.5, -0.5,  0.5, 0.5 )

CLASS: TestPaintBrushStroke ( mock.PaintBrushStroke )
	:MODEL{}

function TestPaintBrushStroke:__init( w, h, x, y )
	self.w = w or 100
	self.h = h or 100
	self.offset = { x or 0, y or 0 }
end

function TestPaintBrushStroke:buildGraphicsProp( canvas )
	local prop = MOAIGraphicsProp.new()
	prop:setDeck( testDeck )
	prop:setScl( self.w, self.h )
	prop:setColor( 1,1,1,0.1 )
	-- prop:setShader( maskShader )
	setPropBlend( prop, 'normal' )
	prop:setLoc( unpack( self.offset ) )
	return prop
end

--------------------------------------------------------------------

local testImage = gii.findDataFile( 'PaintCanvas/brush/NoiseRadialCircle.png' )
local testTex = MOAITexture.new()
testTex:load( testImage, MOAIImage.TRUECOLOR )
local testDeck = MOAISpriteDeck2D.new()
testDeck:setTexture( testTex )
testDeck:setRect( -0.5, -0.5,  0.5, 0.5 )

CLASS: EraserPaintBrushStroke ( mock.PaintBrushStroke )
	:MODEL{}

function EraserPaintBrushStroke:__init( w, h, x, y )
	self.w = w or 100
	self.h = h or 100
	self.offset = { x or 0, y or 0 }
end

function EraserPaintBrushStroke:buildGraphicsProp( canvas )
	local prop = MOAIGraphicsProp.new()
	prop:setDeck( testDeck )
	prop:setScl( self.w, self.h )
	prop:setColor( 0,0,0,0.2 )
	-- prop:setShader( maskShader )
	prop:setBlendMode( MOAIProp.GL_FUNC_REVERSE_SUBTRACT, GL_ONE, GL_ONE )
	prop:setColorMask( false, false, false, true )
	prop:setLoc( unpack( self.offset ) )
	return prop
end


--------------------------------------------------------------------
CLASS: PaintCanvasEditor( mock_edit.EditorEntity )

function PaintCanvasEditor:__init()
	self.targetPaintCanvas = false
end

function PaintCanvasEditor:onLoad()
	local cameraEntity = mock_edit.EditorEntity()
	local cameraCom    = mock_edit.EditorCanvasCamera( _M )
	cameraEntity:attach( cameraCom )
end

function PaintCanvasEditor:findTargetPaintCanvas()
	local selection = gii.getSelection( 'scene' )
	--find a parent animator
	if #selection ~= 1 then --only single selection allowed( for now )
		return nil
	end

	local ent = selection[1]
	if not isInstance( ent, mock.Entity ) then
		return nil
	end

	local map = ent:getComponent( mock.PaintCanvas )
	if map then return map end

	return nil
end

function PaintCanvasEditor:setTargetPaintCanvas( m )
	self.targetPaintCanvas = m
end

function PaintCanvasEditor:getTargetPaintCanvas()
	return self.targetPaintCanvas
end

function PaintCanvasEditor:changeTool( id )
	if not self.targetPaintCanvas then
		mock_edit.alertMessage( 'message', 'no target paintcanvas selected', 'info' )
		return
	end
	if id == 'pen' then		
		mock_edit.getCurrentSceneView():changeCanvasTool( 'paintcanvas.pen' )
	elseif id == 'eraser' then
		mock_edit.getCurrentSceneView():changeCanvasTool( 'paintcanvas.eraser' )
	end
end

function PaintCanvasEditor:clearCanvas()
	if not self.targetPaintCanvas then
		mock_edit.alertMessage( 'message', 'no target paintcanvas selected', 'info' )
		return
	end
	self.targetPaintCanvas:clearAll()
	self.targetPaintCanvas:markDataModified()
	mock_edit.getCurrentSceneView():updateCanvas()
end	

function PaintCanvasEditor:toggleToolRandom( enabled )
	self.randomEnabled = enabled
end


--------------------------------------------------------------------
CLASS: PaintCanvasToolPen ( mock_edit.CanvasTool )
	:MODEL{}

function PaintCanvasToolPen:__init()
	self.pressed = false
	self.action = false
	self.drawFromPos = { 0, 0 }

end

function PaintCanvasToolPen:updateDrawFromPos( x, y )
	self.drawFromPos = { x, y }
end

function PaintCanvasToolPen:getDrawFromPos()
	return unpack( self.drawFromPos )
end

function PaintCanvasToolPen:onMouseDown( btn, x, y )
	if self.pressed then return end
	if btn == 'left' then 
		self.action = 'normal'
		self:_doAction( x, y )

	elseif btn == 'right' then
		self.action = 'optional'
		self:_doAction( x, y )

	else
		return
	end
	self.pressed = btn
end

local function _drawArea( x0, y0, x1, y1, step, func )
	if x0 > x1 then 
		local t = x0
		x0, x1 = x1, t
	end
	if y0 > y1 then 
		local t = y0
		y0, y1 = y1, t
	end
	for y = y0,y1 do
		for x = x0,x1 do
			func( x, y )
		end
	end
end

local function _drawxLine( x0, y0, x1, y1, step, func )	
	local dx = x1 - x0
	local dy = y1 - y0
	step = step or 1
	if math.abs( dx ) > math.abs( dy ) then
		--loop x axis
		local count = math.floor( math.abs( dx ) / step )
		if count == 0 then return end
		local stepY = dy / count
		local stepX = dx > 0 and step or - step
		for i = 0, count do
			local x = i * stepX + x0
			local y = i * stepY + y0
			func( x, y )
		end
	else
		--loop y axis
		local count = math.floor( math.abs( dy ) / step )
		if count == 0 then return end
		local stepX = dx / count
		local stepY = dy > 0 and step or - step
		for i = 0, count do
			local x = i * stepX + x0
			local y = i * stepY + y0
			func( x, y )
		end
	end
end


function PaintCanvasToolPen:onAction( action, canvas, x, y, dragging )
	local size = self:getInputDevice():isShiftDown() and 10 or 50
	if action == 'normal' then
		if self:getInputDevice():isShiftDown() and ( not dragging ) then
			--Draw Line
			-- local brush = editor:getTileBrush()
			-- if brush then
			-- 	local x0, y0 = self:getDrawFromPos()
			-- 	_drawArea( x0, y0, x, y, 1, 
			-- 		function( tx, ty )
			-- 			layer:setTile( tx,ty, brush )
			-- 		end
			-- 	)
			-- end
		else
			local sx, sy = canvas:getScale()
			canvas:addStroke( TestPaintBrushStroke( size/sx, size/sy, x/sx, y/sy ) )
			canvas:update()
			canvas:markDataModified()
			self:updateDrawFromPos( x, y )
		end

	elseif action == 'optional' then
		if self:getInputDevice():isShiftDown() and ( not dragging ) then
			-- local x0, y0 = self:getDrawFromPos()
			-- _drawArea( x0, y0, x, y, 1, 
			-- 	function( tx, ty )
			-- 		layer:setTile( tx,ty, false )
			-- 	end
			-- )
			self:updateDrawFromPos( x, y )
		else
			-- layer:setTile( x,y, false )
			local sx, sy = canvas:getScale()
			canvas:addStroke( EraserPaintBrushStroke( size/sx, size/sy, x/sx, y/sy ) )
			canvas:update()
			canvas:markDataModified()
			self:updateDrawFromPos( x, y )
		end
	end
end

function PaintCanvasToolPen:onMouseUp( btn, x, y )
	if self.pressed ~= btn then return end
	self.pressed    = false
	if self.modified then
		gii.emitPythonSignal( 'entity.modified', editor.targetPaintCanvas )
	end
end

function PaintCanvasToolPen:onMouseMove( x, y )
	if not self.pressed then return end
	self:_doAction( x, y, true )
end

function PaintCanvasToolPen:_doAction( x, y, dragging )
	local canvas = editor:getTargetPaintCanvas()
	if not canvas then
		if not dragging then
			mock_edit.alertMessage( 'message', 'no paint canvas selected', 'info' )
		end
		return false
	end
	local view = mock_edit.getCurrentSceneView()
	local cx, cy = canvas:wndToCanvas( x, y, view:getCameraComponent() )
	self:onAction( self.action, canvas, cx, cy, dragging )
	mock_edit.getCurrentSceneView():updateCanvas()
	self.modified = true
end

mock_edit.registerCanvasTool( 'paintcanvas.pen', PaintCanvasToolPen )


--------------------------------------------------------------------
CLASS: PaintCanvasToolEraser ( PaintCanvasToolPen )

function PaintCanvasToolEraser:onAction( action, canvas, x, y, dragging )
	if action == 'normal' then
		if self:getInputDevice():isShiftDown() and ( not dragging ) then
		-- 	local x0, y0 = self:getDrawFromPos()
		-- 	_drawArea( x0, y0, x, y, 1, 
		-- 		function( tx, ty )
		-- 			layer:setTile( tx,ty, false )
		-- 		end
		-- 	)
			self:updateDrawFromPos( x, y )
		else
			-- layer:setTile( x,y, false )
			local sx, sy = canvas:getScale()
			canvas:addStroke( EraserPaintBrushStroke( 50/sx, 50/sy, x/sx, y/sy ) )
			canvas:update()
			canvas:markDataModified()
			self:updateDrawFromPos( x, y )
		end
	else
	end
end

mock_edit.registerCanvasTool( 'paintcanvas.eraser', PaintCanvasToolEraser )


--------------------------------------------------------------------
editor = scn:addEntity( PaintCanvasEditor() )



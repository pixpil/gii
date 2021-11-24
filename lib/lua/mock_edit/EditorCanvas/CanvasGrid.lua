module 'mock_edit'
--------------------------------------------------------------------
--CanvasGrid
--------------------------------------------------------------------
CLASS: CanvasGrid( EditorEntity )
function CanvasGrid:onLoad()
	self:attach( mock.DrawScript{	priority = -1	} )
	self.gridSize = { 100, 100 }
end

function CanvasGrid:onDraw()
	local context = gii.getCurrentRenderContext()
	local w, h = context:getSize()
	local scl  = context:getScale()
	local x0, y1 = self:wndToWorld( 0, 0 )
	local x1, y0 = self:wndToWorld( w * scl, h * scl )
	
	if w and h then
		--sub grids
		MOAIDraw.setPenWidth( 1 )
		MOAIDraw.setPenColor( .4, .4, .4, .5 )
		local dx = x1-x0
		local dy = y1-y0
		local gw, gh = self.gridSize[1], self.gridSize[2]
		-- x0, y1 = self:wndToWorld( 0, 0 )
		-- x1, y0 = self:wndToWorld( w, h )
		local col = math.ceil( dx/gw )
		local row = math.ceil( dy/gh )
		local cx0 = math.floor( x0/gw ) * gw
		local cy0 = math.floor( y0/gh ) * gh
		for x = cx0, cx0 + col*gw, gw do
			MOAIDraw.drawLine( x, y0, x, y1 )
		end
		for y = cy0, cy0 + row*gh, gh do
			MOAIDraw.drawLine( x0, y, x1, y )
		end

	else
		x0, y0 = -100000, -100000
		x1, y1 =  100000,  100000
	end
	--Axis
	MOAIDraw.setPenWidth( 1 )
	MOAIDraw.setPenColor( .5, .5, .7, .7 )
	MOAIDraw.drawLine( x0, 0, x1, 0 )
	MOAIDraw.drawLine( 0, y0, 0, y1 )

	MOAIDraw.setPenWidth( 1 )
end

function CanvasGrid:getWidth()
	return self.gridSize[1]
end

function CanvasGrid:getHeight()
	return self.gridSize[2]
end

function CanvasGrid:setWidth( w )
	self:setSize( w, self:getHeight() )
end

function CanvasGrid:setHeight( h )
	self:setSize( self:getWidth(), h )
end

function CanvasGrid:setSize( w, h )
	self.gridSize = { w, h }
end

function CanvasGrid:getSize()
	return self.gridSize[1], self.gridSize[2]
end


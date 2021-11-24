module 'mock_edit'

--------------------------------------------------------------------
local function calcAABB( verts )
	local x0,y0,x1,y1
	for i = 1, #verts, 2 do
		local x, y = verts[ i ], verts[ i + 1 ]
		x0 = x0 and ( x < x0 and x or x0 ) or x
		y0 = y0 and ( y < y0 and y or y0 ) or y
		x1 = x1 and ( x > x1 and x or x1 ) or x
		y1 = y1 and ( y > y1 and y or y1 ) or y
	end
	return x0 or 0, y0 or 0, x1 or 0, y1 or 0 
end


--------------------------------------------------------------------
CLASS: CanvasItemEditableLineStripVert ( CanvasItemVert )
	:MODEL{}

function CanvasItemEditableLineStripVert:onMove()
	self.ownerItem:onVertMove( self )
end

function CanvasItemEditableLineStripVert:onMouseDown( btn, x, y )
	if btn == 'right' then
		return self.ownerItem:removeVert( self )
	end
	return CanvasItemEditableLineStripVert.__super.onMouseDown( self, btn, x, y )
end

function CanvasItemEditableLineStripVert:onDraw()
	local size  = self.size
	applyColor( 'vert', self.state )
	MOAIDraw.fillRect( -size/2, -size/2, size, size )
end

local abs = math.abs
local function _align( x, y, x1, y1, tolerance )
	local dx, dy = abs( x-x1 ), abs( y-y1 )
	if dx < dy and dx < tolerance then --snap x
		return true, x1, y
	end
	if dy < tolerance then --snap y
		return true, x, y1
	end
	return false, x, y
end

function CanvasItemEditableLineStripVert:snapMove( x, y, tolerancePx )
	local snapping = self:getInputDevice():isShiftDown()
	if not snapping then return x, y end
	local zoom =  self:getView():getCameraZoom()
	local tolerance = ( tolerancePx or 20 )/zoom
	local item = self.ownerItem
	local verts = item.verts
	local looped = item.looped
	local idx = self.index
	local count = #verts
	local v0 = verts[ looped and ( idx == 1 and count ) or ( idx - 1 ) ]
	local v1 = verts[ looped and ( idx == count and 1 ) or ( idx + 1 ) ]
	local d0, d1
	local x0,y0
	local x1,y1
	if v0 then
		x0,y0 = v0:getLoc()
	end
	if v1 then
		x1,y1 = v1:getLoc()
	end
	local dx0 = x0 and abs( x-x0 ) or math.huge
	local dx1 = x1 and abs( x-x1 ) or math.huge
	local dy0 = y0 and abs( y-y0 ) or math.huge
	local dy1 = y1 and abs( y-y1 ) or math.huge

	local xs, ys
	-- local s0, s1
	if dx0 < dx1 and dx0 < tolerance then
		xs = 0
	elseif dx1 < tolerance then
		xs = 1
	end

	if dy0 < dy1 and dy0 < tolerance then
		ys = 0
	elseif dy1 < tolerance then
		ys = 1
	end
	if not ( xs or ys ) then return x, y end

	if xs == ys then
		if xs == 0 then
			if dx0 < dy0 then 
				ys = dy1 < tolerance and 1 or nil
			else
				xs = dx1 < tolerance and 1 or nil
			end
		end

		if xs == 1 then
			if dx1 < dy1 then 
				ys = dy0 < tolerance and 0 or nil
			else
				xs = dx0 < tolerance and 0 or nil
			end
		end
	end
	x = ( xs == 0 and x0 ) or ( xs == 1 and x1 ) or x
	y = ( ys == 0 and y0 ) or ( ys == 1 and y1 ) or y
	return x, y
	
end

--------------------------------------------------------------------
CLASS: CanvasItemEditableLineStrip ( CanvasItem )

function CanvasItemEditableLineStrip:__init()
	self.vertCount = 0
	self.verts = {}
	self.looped = false
	self.boundRect = {}
	self.showLine = true
end

function CanvasItemEditableLineStrip:isConstantSize()
	return false
end

function CanvasItemEditableLineStrip:onLoad()
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end

function CanvasItemEditableLineStrip:onDraw()
	MOAIDraw.setPenWidth( 1 )
	if self.showLine then
		applyColor 'shape-line'
		local verts = self:getVertCoords( true )
		MOAIDraw.drawLine( verts )
	end

	applyColor 'context-bound'
	MOAIDraw.drawRect( unpack( self.boundRect ) )
end

function CanvasItemEditableLineStrip:onVertMove( vert )
	return self:onPushAttr( self:getVertCoords(), self.looped )
end

function CanvasItemEditableLineStrip:removeVert( vert )
	local idx = table.index( self.verts, vert )
	if idx then
		table.remove( self.verts, idx )
	end
	vert:destroyAllNow()
	self:onVertsUpdate( true )
end

function CanvasItemEditableLineStrip:onVertsUpdate( sync )
	local vertCoords = self:getVertCoords()
	local x0,y0,x1,y1 = calcAABB( vertCoords )
	self.boundRect = { x0,y0,x1,y1 }
	if sync then
		self:onPushAttr( vertCoords, self.looped )
	end
	self:updateVertIndex()
end

function CanvasItemEditableLineStrip:updateShape()
	local verts, looped = self:onPullAttr()
	if not verts then return end
	return self:setShape( verts, looped, false )
end

function CanvasItemEditableLineStrip:getVertCoords( output )
	local coords = {}
	for i, vert in ipairs( self.verts ) do
		local x, y = vert:getLoc()
		local k = ( i - 1 ) * 2
		coords[ k + 1 ] = x
		coords[ k + 2 ] = y
	end
	if self.looped and output then
		table.insert( coords, coords[ 1 ])
		table.insert( coords, coords[ 2 ])
	end
	return coords
end

function CanvasItemEditableLineStrip:setShape( vertCoords, looped, sync )
	self.looped = looped
	local coordCount = #vertCoords
	local vertCount = coordCount/2
	if vertCount ~= #self.verts then
		--update verts
		self:clearSubItems()
		for i = 1, vertCount do
			local vertItem = self:addSubItem( self:createVertItem() )
			vertItem.index = i
			self.verts[ i ] = vertItem
		end
	end
	
	local vertItems = self.verts
	for i = 1, vertCount do
		local k = ( i-1 ) * 2
		local vertItem = vertItems[ i ]
		local x, y = vertCoords[ k + 1 ], vertCoords[ k + 2 ]
		vertItem:setLoc( x, y )
	end
	
	self:onVertsUpdate( sync )
end

function CanvasItemEditableLineStrip:onPullAttr() --coords, looped
	return nil
end

function CanvasItemEditableLineStrip:onPushAttr( coords, looped )
end

function CanvasItemEditableLineStrip:onUpdate()
	self:updateShape()
end

function CanvasItemEditableLineStrip:onMouseDown( btn, x, y )
	if btn == 'left' then
		local newVert = self:tryInsertVert( x, y )
		if newVert then
			self:getManager():setActiveItem( newVert )
			-- if self:getInputDevice():isShiftDown() then
			-- 	newVert:setLoc( newVert:snapMove( x, y, 100000 ) )
			-- end
			newVert:onMouseDown( btn, x, y )
		end
	end
end

function CanvasItemEditableLineStrip:createVertItem()
	return CanvasItemEditableLineStripVert()
end

function CanvasItemEditableLineStrip:addVert( idx, x, y )
	local vert = self:addSubItem( self:createVertItem() )
	vert:setLoc( x, y )
	table.insert( self.verts, idx, vert )
	self:onVertsUpdate( true )
	return vert
end

function CanvasItemEditableLineStrip:updateVertIndex()
	for i, vert in ipairs( self.verts ) do
		vert.index = i
	end
end

function CanvasItemEditableLineStrip:tryInsertVert( x, y )
	local zoom =  self:getView():getCameraZoom()
	local nearTolerance = 20 / zoom
	local appendTolerance = 500 / zoom
	local verts = self.verts
	local count = #verts
	
	local looped = self.looped

	if count <= ( looped and 2 or 1 ) then
	-- if count <= 1 then
		return self:addVert( count + 1, x, y )
	end
	
	local idx0 = looped and 1 or 2
	--find point near segment
	for i = idx0, count do
		local v1 = verts[ i ]
		local v2 = verts[ i == 1 and count or i - 1 ]
		local x1,y1 = v1:getLoc()
		local x2,y2 = v2:getLoc()
		local px,py = projectPointToLine( x1,y1, x2,y2, x,y )
		local dst = distance( px,py, x,y )
		if dst < nearTolerance then
			local newIdx = i == 1 and count + 1 or i 
			return self:addVert( newIdx, px, py )
		end
	end

	if looped then return nil end
	--try append
	local x0,y0 = verts[ 1 ]:getLoc()
	local x1,y1 = verts[ count ]:getLoc()
	local d0 = distance( x0,y0, x, y )
	local d1 = distance( x1,y1, x, y )
	if d0 > appendTolerance and d1 > appendTolerance then
		return nil
	end

	local newIdx = d0 < d1 and 1 or count + 1
	return self:addVert( newIdx, x, y )
	
end


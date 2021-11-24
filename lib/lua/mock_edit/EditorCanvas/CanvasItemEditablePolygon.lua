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
CLASS: CanvasItemEditablePolygonVert ( CanvasItemVert )
	:MODEL{}

function CanvasItemEditablePolygonVert:onMove()
	self.ownerItem:onVertMove( self )
end

function CanvasItemEditablePolygonVert:onMouseDown( btn, x, y )
	if btn == 'right' then
		return self.ownerItem:onVertRemove( self )
	end
	return CanvasItemEditablePolygonVert.__super.onMouseDown( self, btn, x, y )
end

function CanvasItemEditablePolygonVert:snapMove( x, y, tolerancePx )
	local snapping = self:getInputDevice():isShiftDown()
	if not snapping then return x, y end
	local zoom =  self:getView():getCameraZoom()
	local tolerance = ( tolerancePx or 20 )/zoom
	local item = self.ownerItem
	local verts = item.verts
	-- local looped = item.looped
	local idx = self.index
	local count = #verts
	local v0 = verts[ idx == 1 and count or ( idx - 1 ) ]
	local v1 = verts[ idx == count and 1 or ( idx + 1 ) ]
	local d0, d1
	local x0,y0
	local x1,y1
	if v0 then
		x0,y0 = v0:getLoc()
	end
	if v1 then
		x1,y1 = v1:getLoc()
	end
	local dx0 = x0 and math.abs( x - x0 ) or math.huge
	local dx1 = x1 and math.abs( x - x1 ) or math.huge
	local dy0 = y0 and math.abs( y - y0 ) or math.huge
	local dy1 = y1 and math.abs( y - y1 ) or math.huge

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

function CanvasItemEditablePolygonVert:onDraw()
	local size  = self.size
	local shape = self.shape
	if shape == 'box' then
		applyColor( 'vert', self.state )
		MOAIDraw.fillRect( -size/2, -size/2, size, size )
	end
end


--------------------------------------------------------------------
CLASS: CanvasItemEditablePolygon ( CanvasItem )

function CanvasItemEditablePolygon:__init()
	self.vertCount = 0
	self.verts = {}
	self.triangles = false
	self.boundRect = {}
end

function CanvasItemEditablePolygon:isConstantSize()
	return false
end

function CanvasItemEditablePolygon:onLoad()
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end

function CanvasItemEditablePolygon:onDraw()
	MOAIDraw.setPenWidth( 1 )
	local triangles = self.triangles
	if triangles then
		applyColor 'shape-fill'
		for i, tri in ipairs( self.triangles ) do
			MOAIDraw.fillFan( unpack( tri ) )
		end
	end
	applyColor 'shape-line'
	local verts = self:getVertCoords( true )
	MOAIDraw.drawLine( verts )

	applyColor 'context-bound'
	MOAIDraw.drawRect( unpack( self.boundRect ) )
end

function CanvasItemEditablePolygon:onVertMove( vert )
	return self:onPushAttr( self:getVertCoords() )
end

function CanvasItemEditablePolygon:onVertRemove( vert )
	if #self.verts > 3 then
		local idx = table.index( self.verts, vert )
		if idx then
			table.remove( self.verts, idx )
		end
		vert:destroyAllNow()
		self:onVertsUpdate( true )
	else
		_warn( 'too few polygon verts!' )
	end
end

function CanvasItemEditablePolygon:onVertsUpdate( sync )
	local vertCoords = self:getVertCoords()
	local x0,y0,x1,y1 = calcAABB( vertCoords )
	self.boundRect = { x0,y0,x1,y1 }
	self.drawScript:setRect( x0,y0,x1,y1 )
	if sync then
		self:onPushAttr( vertCoords )
	end
	self:updateVertIndex()
end

function CanvasItemEditablePolygon:updateVertIndex()
	for i, vert in ipairs( self.verts ) do
		vert.index = i
	end
end

function CanvasItemEditablePolygon:updateShape()
	local verts = self:onPullAttr()
	if not verts then return end
	return self:setShape( verts, false )
end

function CanvasItemEditablePolygon:getVertCoords( looped )
	local coords = {}
	for i, vert in ipairs( self.verts ) do
		local x, y = vert:getLoc()
		local k = ( i - 1 ) * 2
		coords[ k + 1 ] = x
		coords[ k + 2 ] = y
	end
	if looped then
		table.insert( coords, coords[ 1 ])
		table.insert( coords, coords[ 2 ])
	end
	return coords
end

function CanvasItemEditablePolygon:setShape( vertCoords, sync )
	local coordCount = #vertCoords
	local vertCount = coordCount/2
	if vertCount ~= #self.verts then
		--update verts
		self:clearSubItems()
		for i = 1, vertCount do
			local vertItem = self:addSubItem( CanvasItemEditablePolygonVert() )
			vertItem.idx = i
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

function CanvasItemEditablePolygon:onPullAttr()
	return nil
end

function CanvasItemEditablePolygon:onPushAttr( coords )
end

function CanvasItemEditablePolygon:onUpdate()
	self:updateShape()
end

function CanvasItemEditablePolygon:onMouseDown( btn, x, y )
	if btn == 'left' then
		local newVert = self:tryInsertVert( x, y )
		if newVert then
			self:getManager():setActiveItem( newVert )
			newVert:onMouseDown( btn, x, y )
		end
	end
end

function CanvasItemEditablePolygon:tryInsertVert( x, y )
	local tolerance = 20 / self:getView():getCameraZoom()
	local count = #self.verts
	local verts = self.verts
	for i = 1, count do
		local v1 = verts[ i ]
		local v2 = verts[ i == 1 and count or i - 1 ]
		local x1,y1 = v1:getLoc()
		local x2,y2 = v2:getLoc()
		local px,py = projectPointToLine( x1,y1, x2,y2, x,y )
		local dst = distance( px,py, x,y )
		if dst < tolerance then
			local newIdx = i == 1 and count + 1 or i
			return self:addVert( newIdx, px,py)			
		end
	end
end

function CanvasItemEditablePolygon:addVert( idx, x, y )
	local newVert = self:addSubItem( CanvasItemEditablePolygonVert() )
	newVert:setLoc( x, y )
	table.insert( self.verts, idx, newVert )
	self:onVertsUpdate( true )
	return newVert
end


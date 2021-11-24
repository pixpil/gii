module 'mock_edit'

--------------------------------------------------------------------
CLASS: CanvasItemEditableSegment ( CanvasItem )

function CanvasItemEditableSegment:__init()
	self.x0 = 0
	self.y0 = 0
	self.x1 = 0
	self.y1 = 0
end

function CanvasItemEditableSegment:onLoad()
	self.vertA = self:addSubItem( CanvasItemVert() )
	self.vertB = self:addSubItem( CanvasItemVert() )

	self.vertA.onMove = function( vert ) return self:onVertMove( 'A' ) end
	self.vertB.onMove = function( vert ) return self:onVertMove( 'B' ) end
	self.vertA:setShape( 'circle' )
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end

function CanvasItemEditableSegment:isConstantSize()
	return false
end

function CanvasItemEditableSegment:onDraw()
	applyColor 'shape-line'
	MOAIDraw.drawLine( self.x0, self.y0, self.x1, self.y1 )
end

function CanvasItemEditableSegment:onVertMove( id )
	local vertA = self.vertA
	local vertB = self.vertB
	if id == 'A' then
		local x0, y0 = vertA:getLoc()
		return self:setShape( x0, y0, self.x1, self.y1, true )
	elseif id == 'B' then
		local x1, y1 = vertB:getLoc()
		return self:setShape( self.x0, self.y0, x1, y1, true )
	end
end

function CanvasItemEditableSegment:updateShape()
	local x0, y0, x1, y1 = self:onPullAttr()
	if not x0 then return end
	return self:setShape( x0, y0, x1, y1, false )
end

function CanvasItemEditableSegment:setShape( x0, y0, x1, y1, sync )
	self.vertA:setLoc( x0, y0 )
	self.vertB:setLoc( x1, y1 )
	self.x0, self.y0 = x0, y0
	self.x1, self.y1 = x1, y1
	self.drawScript:setBounds( x0,y0,0, x1,y1,1 )
	if sync then
		self:onPushAttr( x0, y0, x1, y1 )
	end
end

function CanvasItemEditableSegment:onPullAttr()
	return nil
end

function CanvasItemEditableSegment:onPushAttr( x, y, x1, y1 )
end

function CanvasItemEditableSegment:onUpdate()
	self:updateShape()
end
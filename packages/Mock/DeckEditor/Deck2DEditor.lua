--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------
CLASS: Deck2DEditor( mock_edit.EditorEntity )

function Deck2DEditor:onLoad()
	self:attach( mock.InputScript{ device = scn:getEditorInputDevice() } )
	self:attach( mock.DrawScript{ priority = 1000 } )

	self.currentDeck = false

	self.previewProp = MOAIGraphicsProp.new()
	self.previewGridProp = MOAIGraphicsGridProp.new()
	self.previewGrid = MOAIGrid.new()
	
	setPropBlend( self.previewProp, 'alpha' )
	setPropBlend( self.previewGridProp, 'alpha' )

	self:_attachProp( self.previewGridProp )
	self:_attachProp( self.previewProp )

	self.preview = self.previewProp

	self.polygonEditor = self:addChild( PolygonEditor() )
	self.alphaView = false
end

function Deck2DEditor:setPreviewingGrid( isGrid )
	if not isGrid then
		self.preview = self.previewProp
	else
		self.preview = self.previewGridProp
	end

	self.previewProp:setVisible( not isGrid )
	self.previewGridProp:setVisible( isGrid )
end

function Deck2DEditor:selectDeck( deck )
	self.currentDeck = deck
	
	local previewDeck = deck and deck:getMoaiDeck()
	local dtype = deck.type

	self:setPreviewingGrid( false )
	if dtype == 'tileset' or dtype == 'quad_array' then
		self:setPreviewingGrid( true )
		self.preview:setGrid( self.previewGrid )
	end

	if dtype == 'stretchpatch' then
		self.preview:setScl( 2, 2, 2 )
	end

	if dtype == 'polygon' then
		self.polygonEditor:setEnabled( true )
		self.polygonEditor:setDeck( deck )
		previewDeck = self.polygonEditor:getPreviewDeck()
	else
		self.polygonEditor:setEnabled( false )
		self.polygonEditor:setDeck( false )
	end

	self.preview:setDeck( previewDeck )
	self:updateDeck()
end

function Deck2DEditor:updateDeck( )
	local deck = self.currentDeck
	self.currentDeck:update()
	if deck.type == 'tileset' then		
		local grid = self.previewGrid
		local col, row = deck.col, deck.row
		local tw , th  = deck.tw , deck.th
		local sp = deck.spacing
		grid:setSize( col, row, tw + sp, th + sp, 0, 0, tw, th)
		local t = 1
		for j = row, 1, -1 do
			for i = 1, col do
				grid:setTile( i, j, t )
				t=t+1
			end
		end
	elseif deck.type == 'quad_array' then
		local grid = self.previewGrid
		local col, row = deck.col, deck.row
		local tw , th  = deck.tw , deck.th
		local sp = deck.spacing
		grid:setSize( col, row, tw + sp, th + sp, 0, 0, 1, 1)
		local t = 1
		local count = deck.count
		if count <= 0 then count = col*row end
		for j = row, 1, -1 do
			for i = 1, col do				
				if t <= count then
					grid:setTile( i, j, t )
				else
					grid:setTile( i, j, 0 )
				end
				t=t+1
			end
		end
	end
	self:updatePreviewShader()
	self.preview:forceUpdate()
	updateCanvas()
	updateEditor()
end

function Deck2DEditor:setOrigin( direction )
	if not self.currentDeck then return end
	local x0,y0,z0, x1,y1,z1 = self.preview:getBounds()
	local w, h =x1-x0, y1-y0
	x0,x1 = -w/2, w/2
	y0,y1 = h/2, -h/2
	local ox, oy
	if     direction == 'E'  then
		ox, oy = x1,  0
	elseif direction == 'W'  then
		ox, oy = x0,  0
	elseif direction == 'N'  then
		ox, oy = 0,  y0
	elseif direction == 'S'  then
		ox, oy = 0,  y1
	elseif direction == 'SE' then
		ox, oy = x1,  y1
	elseif direction == 'SW' then
		ox, oy = x0,  y1
	elseif direction == 'NE' then
		ox, oy = x1,  y0
	elseif direction == 'NW' then
		ox, oy = x0,  y0
	elseif direction == 'C' then
		ox, oy = 0, 0
	else
		ox, oy = 0, 0
	end
	self.currentDeck:setOrigin( ox, oy )
	self:updateDeck()
end

--------------------------------------------------------------------
function Deck2DEditor:onMouseMove()
	if not self.currentDeck then return end	
	if scn:getEditorInputDevice():isMouseDown('right') then
		local dx , dy = scn:getEditorInputDevice():getMouseDelta()
		local zoom = scn:getCameraZoom()
		dx = dx/zoom
		dy = dy/zoom
		local ox,oy = self.currentDeck:getOrigin()
		if ox then
			self.currentDeck:setOrigin( ox + dx, oy - dy )
		end
		self:updateDeck()
	end	
	if scn:getEditorInputDevice():isMouseDown('left') then
	end
end

--------------------------------------------------------------------
function Deck2DEditor:onMouseDown( btn, x, y )
	if btn == 'right' then
	end
end

--------------------------------------------------------------------
function Deck2DEditor:onDraw()
	local deck = self.currentDeck
	if not deck then return end
	if deck.type == 'tileset' or deck.type == 'quad_array' then
		local col, row = deck.col, deck.row
		local tw , th  = deck.tw , deck.th
		local sp = deck.spacing
		MOAIDraw.setPenColor(0,1,0,0.3)
		for i = 0, col-1 do
			for j = 0, row-1 do
				local x , y
				x = i * (tw + sp)
				y = j * (th + sp)
				MOAIDraw.drawRect( x, y, x+tw, y+th )
			end
		end
		return
	end

	MOAIDraw.setPenColor(0,1,0,0.4)
	local x0,y0,z0, x1,y1,z1 = self.preview:getWorldBounds()
	MOAIDraw.drawRect(x0,y0,x1,y1)

	if deck.type == 'stretchpatch' then
		MOAIDraw.setPenColor(1,0,0,0.4)
		local extent = 20
		local r1,r3 = deck.top * deck.h,  deck.bottom * deck.h
		local c1,c3 = deck.left * deck.w, deck.right * deck.w

		--rows
		-- local y= y0 ;      MOAIDraw.drawLine( x0-extent, y, x1+extent, y )
		local y= r1 + y0;  MOAIDraw.drawLine( x0-extent, y, x1+extent, y )
		local y= y1 - r3;  MOAIDraw.drawLine( x0-extent, y, x1+extent, y )
		-- local y= y1 ;      MOAIDraw.drawLine( x0-extent, y, x1+extent, y )

		--columns
		-- local x= x0 ;      MOAIDraw.drawLine( x, y0-extent, x, y1+extent )
		local x= c1 + x0;  MOAIDraw.drawLine( x, y0-extent, x, y1+extent )
		local x= x1 - c3;  MOAIDraw.drawLine( x, y0-extent, x, y1+extent )
		-- local x= x1 ;      MOAIDraw.drawLine( x, y0-extent, x, y1+extent )
	end
end

function Deck2DEditor:addItem( item )
	if not self.editingPack then return end
	local dtype = item['type']
	local src   = item['src']
	local name  = item['name']
	local deck = self.editingPack:addDeck( name, dtype, src )
	return deck
end

function Deck2DEditor:removeItem( item )
	if not self.editingPack then return end
	self.editingPack:removeDeck( item )
end

function Deck2DEditor:openPack( path )
	local pack = mock.loadAsset( path )
	if not pack then pack = mock.Deck2DPack() end
	self.editingPack = pack
	return pack
end

function Deck2DEditor:savePack( path )
	if not self.editingPack then return end
	mock.serializeToFile( self.editingPack, path )
end

function Deck2DEditor:toggleAlphaView( toggled )
	self.alphaView = toggled
	self:updatePreviewShader()
	updateCanvas()
end

function Deck2DEditor:updatePreviewShader()
	if self.alphaView then
		self.preview:setShader( hardAlphaShader )
	else
		self.preview:setShader( MOAIShaderMgr.getShader( MOAIShaderMgr.DECK2D_SHADER ) )
	end
end

--------------------------------------------------------------------
local vertexSize = 5

CLASS: VertexHandle( mock_edit.CanvasHandle )
function VertexHandle:__init()
	self.selected = false
	self:attach( mock.DrawScript{ priority = 1000 } )
end

function VertexHandle:onDraw()
	local z = scn:getEditorCamera():com():getZoom()
	local r = vertexSize / z
	MOAIDraw.setPenWidth( 1 )
	if self.selected then
		MOAIDraw.setPenColor( 1,1,0,1 )
	else
		MOAIDraw.setPenColor( 0,1,0,1 )
	end
	MOAIDraw.fillCircle( 0, 0, r )
	MOAIDraw.setPenColor( 1,1,1,1 )
	MOAIDraw.drawCircle( 0, 0, r )
end

function VertexHandle:inside( x, y )
	local x0,y0 = self:getLoc()
	return distance( x0,y0, x,y ) < vertexSize + 5
end

--------------------------------------------------------------------
CLASS: Polygon ( mock_edit.EditorEntity )
	:MODEL{}
function Polygon:__init()
	self.vertexList = {}
	self.triangles  = false
	self.closed = false
	self:attach( mock.DrawScript{ priority = 500 } )
end

function Polygon:onLoad()
end

function Polygon:addVertex( x, y, index )
	local v = self:addChild( VertexHandle() )
	v:setLoc( x, y )
	if index then
		table.insert( self.vertexList, index, v )
	else
		table.insert( self.vertexList, v )
	end
	v:forceUpdate()
	self:triangulate()
	updateCanvas()
	return v
end

function Polygon:closePolygon()
	if #self.vertexList < 3 then return false end
	self.closed = true
	self:triangulate()
	return true
end

function Polygon:triangulate()
	if not self.closed then return end
	local coords = self:getVertexCoords()
	local verts = triangulatePolygon( gii.tableToList( coords ) )
	verts = gii.listToTable( verts )
	local triangles = {}
	for i = 1, #verts, 6 do
		local tri = {}
		for j = i, i + 6 do
			table.insert( tri, verts[ j ] )
		end
		table.insert( triangles, tri )
	end
	self.triangles = triangles
end

function Polygon:findVertex( x, y )
	for i, v in ipairs( self.vertexList ) do
		if v:inside( x, y ) then
			return v
		end
	end
end

function Polygon:removeVertex( v1 )
	for i, v in ipairs( self.vertexList ) do
		if v == v1 then 
			v:destroy()
			table.remove( self.vertexList, i )
			if #self.vertexList < 3 then 
				self.closed = false
				self.triangles = false
			else
				self:triangulate()
			end
			updateCanvas()
			return
		end
	end
end

function Polygon:tryInsertVertex( x, y )
	local count = #self.vertexList
	for i, v1 in ipairs( self.vertexList ) do
		local v2 = self.vertexList[ i == 1 and count or i - 1 ]
		local x1,y1 =v1:getLoc()
		local x2,y2 =v2:getLoc()
		local px,py = projectPointToLine( x1,y1, x2,y2, x,y )
		local dst = distance( px,py, x,y )
		if dst < 10 then
			local newVertex = self:addVertex( px, py, i == 1 and count + 1 or i )
			return newVertex
		end
	end
end

function Polygon:getVertexCoords( loop )
	local verts = {}
	for i, v in ipairs( self.vertexList ) do
		local x, y = v:getLoc()
		table.insert( verts, x )
		table.insert( verts, y )
	end
	if loop and self.closed then
		table.insert( verts, verts[1] )
		table.insert( verts, verts[2] )
	end
	return verts
end


function Polygon:onDraw()
	local triangles = self.triangles
	if triangles then
		MOAIDraw.setPenWidth( 1 )
		MOAIDraw.setPenColor( 0,0,1,0.4 )
		for i,tri in ipairs( self.triangles ) do
			MOAIDraw.fillFan( unpack( tri ) )
		end
		-- MOAIDraw.setPenColor( 0,0,1,0.2 )
		-- for i,tri in ipairs( self.triangles ) do
		-- 	MOAIDraw.drawLine( tri )
		-- end
	end
	MOAIDraw.setPenColor( 1,0,1,1 )
	MOAIDraw.setPenWidth( 2 )
	local verts = self:getVertexCoords( true )
	MOAIDraw.drawLine( verts )

	MOAIDraw.setPenWidth( 1 )
end

--------------------------------------------------------------------
CLASS: PolygonEditor( mock_edit.EditorEntity )
function PolygonEditor:onLoad()
	self.polygons = {}
	self:attach( mock.InputScript{ device = scn:getEditorInputDevice() } )
	self.previewDeck    = false
	self.currentPolygon = false
	self.currentVertex  = false
	self.dragging       = false
	self.bounds         = {0,0,100,100}
end

function PolygonEditor:addPolygon()
	local p = self:addChild( Polygon() )
	return p
end

function PolygonEditor:pickPolygon( x, y )
end

function PolygonEditor:onMouseDown( btn, x, y )
	if not self.enabled then return end
	if btn == 'left' then
		x, y = self:wndToWorld( x, y )
		
		if not self.currentPolygon then
			self.currentPolygon = self:addPolygon()			
		end	
		
		if self.currentVertex then
			if self.currentVertex == self.currentPolygon.vertexList[1] then 
				self.currentPolygon:closePolygon()
				self:updateDeck()
				updateCanvas()
			end
		else
			x, y = self.currentPolygon:worldToModel( x, y )

			if not self.currentPolygon.closed then
				if not self:inside( x, y ) then return end
				local v = self.currentPolygon:addVertex( x, y )
				self:setCurrentVertex( v )
				self:updateDeck()
			else --try insert
				local v = self.currentPolygon:tryInsertVertex( x, y )
				if v then self:setCurrentVertex( v ) end
				self:updateDeck()
			end
		end
		self.dragging = self.currentVertex ~= false
	end
end

function PolygonEditor:onKeyDown( key )
	if self.dragging then return end
	if key == 'delete' and self.currentVertex then
		self.currentPolygon:removeVertex( self.currentVertex )
		self:setCurrentVertex( false )
		self:updateDeck()
	end
end


function PolygonEditor:setCurrentVertex( v )
	v = v or false
	if self.currentVertex == v then return end
	if self.currentVertex then self.currentVertex.selected = false end
	self.currentVertex = v
	if v then v.selected = true end
	updateCanvas()
end

function PolygonEditor:limitPos( x, y )
	local bounds = self.bounds
	x = clamp( x, bounds[1], bounds[3] )
	y = clamp( y, bounds[2], bounds[4] )
	return x, y
end

function PolygonEditor:inside( x, y )
	local bounds = self.bounds
	return 
		between( x, bounds[1], bounds[3] ) and 
		between( y, bounds[2], bounds[4] )
end


function PolygonEditor:onMouseMove( x, y )
	x, y = self:wndToWorld( x, y )
	if not self.dragging then 		
		local v = self:findVertex( x, y )
		self:setCurrentVertex( v )
	else
		x, y = self:limitPos( x, y )
		x, y = self.currentPolygon:worldToModel( x, y )
		self.currentVertex:setLoc( x, y )
		self.currentPolygon:triangulate()
		updateCanvas()
		self:updateDeck()
	end
end

function PolygonEditor:onMouseUp( btn, x, y )
	if btn == 'left' then
		x, y = self:wndToWorld( x, y )
		self.dragging = false
		self:setCurrentVertex( self:findVertex( x, y ) )
	end
end

function PolygonEditor:findVertex( x, y )
	return self.currentPolygon and self.currentPolygon:findVertex( x, y )
end

-- function PolygonEditor:wndToWorld( x, y )
-- 	return scn.cameraCom:wndToWorld( x, y )
-- end

function PolygonEditor:setEnabled( e )
	self.enabled = e
	self:setVisible( e )
end

function PolygonEditor:setDeck( deck )
	self.currentDeck = deck
	if deck then
		local previewDeck = mock.Quad2D()
		local tex = self.currentDeck:getTexture()
		previewDeck:setTexture( tex )
		self.previewDeck = previewDeck
		local bounds = { previewDeck:getRect() }	
		self.bounds = bounds
		--load triangles
		if self.currentPolygon then self.currentPolygon:destroy() end

		local poly = self:addPolygon()
		self.currentPolygon = poly

		local polyline = deck.polyline
		if not polyline then
			local x,y,x1,y1 = unpack( bounds )
			polyline = {
				x, y,
				x1, y,
				x1, y1,
				x, y1,
			}
		end
		for i = 1, #polyline, 2 do
			local x, y = polyline[i], polyline[i+1]
			poly:addVertex( x, y )
		end
		poly:closePolygon()
	end

end

local insert = table.insert
function PolygonEditor:updateDeck()
	local poly = self.currentPolygon

	self.currentDeck.polyline = poly:getVertexCoords()

	local triangles = poly.triangles
	if not triangles then return end

	local w, h = self.previewDeck:getSize()
	local verts = {}
	for i, tri in ipairs( triangles ) do
		for j = 1, 6, 2 do
			local x,y = tri[j], tri[j+1]
			insert( verts, x )
			insert( verts, y )
			local u,v = ( x + w/2 ) / w, ( y + h/2 ) / h
			insert( verts, u )
			insert( verts, v )
		end
	end
	self.currentDeck.vertexList = verts
	self.currentDeck:update()
end

function PolygonEditor:getPreviewDeck()
	return self.previewDeck:getMoaiDeck()	
end

--------------------------------------------------------------------
editor = scn:addEntity( Deck2DEditor() )

function loadAsset( data )
	local modelName = data['model']
	local deck
	if modelName == 'Quad2D' then
		deck = Quad2D()
	elseif modelName == 'Tileset' then
		deck = Tileset()
	elseif modelName == 'StretchPatch' then
		deck = StretchPatch()
	end
	mock.deserialize( deck, data )
	return deck
end

function addItem( item )
	return editor:addItem( item )
end

function setOrigin( direction )
	editor:setOrigin( direction )	
end

function selectDeck( deck )
	editor:selectDeck( deck )
end

function updateDeck( )
	editor:updateDeck()
end

function renameDeck( deck, name )
	deck:setName( name )
	editor:updateDeck()
end

--------------------------------------------------------------------
--res
--------------------------------------------------------------------
hardAlphaShader = mock_edit.loadShader{
	vsh=[[
		in vec4 position;
		in vec2 uv;
		in vec4 color;

		out MEDP vec2 uvVarying;

		void main () {
			gl_Position = position;
			uvVarying = uv;
		}
	]],

	fsh=[[
		in MEDP vec2 uvVarying;
		uniform sampler2D sampler;
		out MEDP vec4 FragColor;

		void main () {
			LOWP vec4 tex = texture ( sampler, uvVarying );	
			if( tex.a > 0.0 ) {
				FragColor = vec4( 1.0, 1.0, 1.0, 1.0 );
			} else {
				FragColor = vec4( 1.0, 0.0, 0.0, 0.2 );
			}
		}
	]]
};


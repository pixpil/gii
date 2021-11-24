module 'mock_edit'

addColor( 'path_vert', hexcolor( '#47beff', 1 ) )
addColor( 'path_vert:selected', hexcolor( '#ffff7a', 1 ) )
addColor( 'path_line', hexcolor( '#f2ffff', 1 ) )

--------------------------------------------------------------------
CLASS: PathGizmo( Gizmo )

function PathGizmo:__init( path )
	self.path = path
	self.transform = MOAITransform.new()
	inheritTransform( self.transform, path._entity:getProp( 'physics' ) )
end

function PathGizmo:onLoad()
	self.drawScript = self:attach( mock.DrawScript() )
	self.drawScript:setBlend( 'alpha' )
end

local drawLine = MOAIDraw.drawLine
function PathGizmo:onDraw()
	GIIHelper.setVertexTransform( self.transform )
	applyColor 'path_line'
	local verts = self.path:getVertCoords()
	drawLine( verts )
end

--------------------------------------------------------------------
--Install
mock.Path.onBuildSelectedGizmo = function( self )
	return PathGizmo( self )
end


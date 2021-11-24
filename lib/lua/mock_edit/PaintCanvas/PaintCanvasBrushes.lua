
--------------------------------------------------------------------
local smoothTex = MOAITexture.new()
smoothTex:load( 'game/test/SmoothRect.png', 0 )
local quadDeck = MOAISpriteDeck2D.new()
quadDeck:setTexture( smoothTex )
quadDeck:setRect( -0.5, -0.5,  0.5, 0.5 )

CLASS: TestBrushStroke2 ( mock.PaintBrushStroke )
	:MODEL{}

function TestBrushStroke2:__init( w, h, x, y )
	self.w = w or 100
	self.h = h or 100
	self.offset = { x or 0, y or 0 }
end

function TestBrushStroke2:buildGraphicsProp( canvas )
	local prop = MOAIGraphicsProp.new()
	prop:setDeck( quadDeck )
	prop:setScl( self.w, self.h )
	prop:setColor( 1,1,1,1 )
	setPropBlend( prop, 'alpha' )
	prop:setLoc( unpack( self.offset ) )
	return prop
end

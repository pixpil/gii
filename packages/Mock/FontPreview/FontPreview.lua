--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

CLASS: FontPreview ( mock.Entity )
--------------------------------------------------------------------


function FontPreview:__init()
	self.currentFont = false
	self.currentFontSize = 20
	self.currentText  ='Hello, GII!'
end

function FontPreview:onLoad()
	
	local textbox = MOAITextBox.new()
	self.textbox = textbox
	textbox:setYFlip( true )
	setPropBlend( textbox, 'alpha' )
	textbox:setShader( MOAIShaderMgr.getShader(MOAIShaderMgr.FONT_SHADER) )
	textbox:setStyle( gii.getDefaultStyle() )
	textbox:setString( self.currentText )
	self:_attachProp( textbox )

end

function FontPreview:updateText()
	local style = MOAITextStyle.new()
	style:setFont( self.currentFont )
	style:setSize( self.currentFontSize )
	style:setColor( 1,1,1,1 )

	local textbox = self.textbox
	textbox:setStyle( style )
	textbox:setString( self.currentText )
	textbox:forceUpdate()

	updateCanvas()
end

function FontPreview:setFont( path )
	local textbox = self.textbox
	
	local font, node = mock.loadAsset( path )
	if not font then return end

	if node.type == 'font_bmfont' then
		textbox:setShader( MOAIShaderMgr.getShader(MOAIShaderMgr.DECK2D_SHADER) )
	else
		textbox:setShader( MOAIShaderMgr.getShader(MOAIShaderMgr.FONT_SHADER) )
	end
	self.currentFont = font
	self.currentFontSize = font.size or self.currentFontSize
	self:updateText()
end

function FontPreview:setFontSize( size )
	self.currentFontSize = size
	self:updateText()
end

function FontPreview:setText( text )
	self.currentText = text
	self:updateText()
end

function FontPreview:onResize( w, h )
	self.textbox:setRect(-w/2 ,-h/2, w/2, h/2)	
end

--------------------------------------------------------------------
preview = scn:addEntity( FontPreview() )
--------------------------------------------------------------------

function onResize(w,h)
	preview:onResize( w, h )
end

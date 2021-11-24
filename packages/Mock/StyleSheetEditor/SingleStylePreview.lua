--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------
CLASS: StyleItemPreview ( mock_edit.EditorEntity )
	:MODEL{}

function StyleItemPreview:onLoad()
	self.textLabel = self:attach( mock.TextLabel() )
	self.textLabel:setSize( 500, 100 )
	self.textLabel:setAlignment( 'center' )
	self.textLabel:setText( 'hello!, gii' )
	self:setVisible( false )

end

function StyleItemPreview:setStyle( s )
	if not s then
		self:setVisible( false )
		self.textLabel.box:setStyle( mock.getFallbackTextStyle() )
	else
		self:setVisible( true )
		self.textLabel.box:setStyle( s:getMoaiTextStyle() or mock.getFallbackTextStyle() )
	end
	updateCanvas()
end

function StyleItemPreview:setPreviewText( t )
	self.textLabel:setText( t )
	updateCanvas()
end

function StyleItemPreview:updateStyle()
	self.textLabel.box:setYFlip( false ) --hacking to force re-layout
	updateCanvas()
end

preview = scn:addEntity( StyleItemPreview() )

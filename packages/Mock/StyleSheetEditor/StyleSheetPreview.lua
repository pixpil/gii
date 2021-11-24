--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

CLASS: StyleSheetPreview ( mock_edit.EditorEntity )
	:MODEL{}

function StyleSheetPreview:onLoad()
	self:attach( mock.InputScript{ device = scn:getEditorInputDevice() } )
	self:attach( mock.DrawScript{ priority = 1000 } )

	self.styleSheet = false
	self.textLabel = self:attach( mock.TextLabel() )
	self.textLabel:setSize( 200, 200 )
	self.textLabel:setText( 'hello!' )
	self:setVisible( false )
end

function StyleSheetPreview:open( path )
	self.styleSheet = mock.loadAsset( path )
	if self.styleSheet then
		self.textLabel:setStyleSheet( path )
	end
	self:setVisible( true )
	updateCanvas()
	return self.styleSheet
end

function StyleSheetPreview:save( path )
	if not self.styleSheet then return end
	mock.serializeToFile( self.styleSheet, path )
end

function StyleSheetPreview:close()
	self.styleSheet = false
	self:setVisible( false )
end

function StyleSheetPreview:setPreviewText( t )
	self.textLabel:setText( t )
	updateCanvas()
end

function StyleSheetPreview:setAlignment( a )
	self.textLabel:setAlignment( a )
	updateCanvas()
end

local getBuiltinShader          = MOAIShaderMgr. getShader
local DECK2D_TEX_ONLY_SHADER    = MOAIShaderMgr. DECK2D_TEX_ONLY_SHADER
local DECK2D_SHADER             = MOAIShaderMgr. DECK2D_SHADER
local FONT_SHADER               = MOAIShaderMgr. FONT_SHADER

function StyleSheetPreview:setShader( s )
	if s == 'tex' then
		self.textLabel.box:setShader( getBuiltinShader( DECK2D_SHADER ) )
	else
		self.textLabel.box:setShader( getBuiltinShader( FONT_SHADER ) )
	end
end

----

function StyleSheetPreview:addStyle()
	return self.styleSheet:addStyle()
end

function StyleSheetPreview:removeStyle( s )
	return self.styleSheet:removeStyle( s )
end

function StyleSheetPreview:cloneStyle( s )
	return self.styleSheet:cloneStyle( s )
end

function StyleSheetPreview:renameStyle( s, name )
	s.name = name
end

function StyleSheetPreview:updateStyles()
	self.styleSheet:updateStyles()
	self.textLabel.box:setYFlip( false ) --hacking to force re-layout
	updateCanvas()
end

--------------------------------------------------------------------
preview = scn:addEntity( StyleSheetPreview() )
module 'mock_edit'
--------------------------------------------------------------------
--EditorCanvasScene
--------------------------------------------------------------------
CLASS: EditorCanvasScene ( mock.Scene )
function EditorCanvasScene:__init( env, options )
	self.FLAG_EDITOR_SCENE = true
	self.env = env or getfenv( 2 )
	self.options = options or {}
end

function EditorCanvasScene:getOption( key, default )
	local v = self.options[ key ]
	if v == nil then return default end
	return v
end

function EditorCanvasScene:getEnv()
	return self.env
end

function EditorCanvasScene:initLayers()
	EditorCanvasScene.__super.initLayers( self )
	self.defaultLayer = assert( self:getLayer( '_GII_EDITOR_LAYER' ) )
end

function EditorCanvasScene:getLayerSources()
	if self:getOption( 'use_game_layer', false ) then
		local layers = EditorCanvasScene.__super.getLayerSources( self )
		local hasEditorLayer = false
		for i, layer in ipairs( layers ) do
			if layer.name == '_GII_EDITOR_LAYER' then hasEditorLayer = true end
		end
		if not hasEditorLayer then
			local editorLayer = mock.Layer( '_GII_EDITOR_LAYER' )
			editorLayer.priority = 1000000
			layers = table.join( { editorLayer }, layers )
		end
		return layers
	else
		return { mock.Layer( '_GII_EDITOR_LAYER' ) }
	end
end

function EditorCanvasScene:getParentActionRoot()
	local ctx = gii.getCurrentRenderContext()
	return ctx.actionRoot
end

function EditorCanvasScene:updateCanvas()
	self.env.updateCanvas()
end

function EditorCanvasScene:updateWidget()
	self.env.updateWidget()
end

function EditorCanvasScene:getCanvasSize()
	local s = self.env.getCanvasSize()
	return s[0], s[1]
end

function EditorCanvasScene:hideCursor()
	return self.env.hideCursor()
end

function EditorCanvasScene:setCursor( id )
	return self.env.setCursor( id )
end

function EditorCanvasScene:showCursor()
	return self.env.showCursor()
end

function EditorCanvasScene:setCursorPos( x, y )
	return self.env.setCursorPos( x, y )
end

function EditorCanvasScene:startUpdateTimer( fps )
	return self.env.startUpdateTimer( fps )
end

function EditorCanvasScene:stopUpdateTimer()
	return self.env.stopUpdateTimer()
end

function EditorCanvasScene:getEditorInputDevice()
	return getEditorCanvasInputDevice( self.env )
end

function EditorCanvasScene:getMainRenderContext()
	return self.env.getMockRenderContext()
end

module 'mock_edit'

--------------------------------------------------------------------
CLASS: SimpleEditorCanvasScene ( EditorCanvasScene )
	:MODEL{}

function SimpleEditorCanvasScene:onLoad()
	self.canvasView = self:addEntity( CanvasView( self.env ) )
end

function SimpleEditorCanvasScene:getView()
	return self.canvasView
end

function SimpleEditorCanvasScene:getEditorCamera()
	return self.canvasView:getCamera()
end

function SimpleEditorCanvasScene:getCameraComponent()
	return self.canvasView:getCameraComponent()
end

function SimpleEditorCanvasScene:getCameraZoom()
	return self:getCameraComponent():getZoom()
end

function SimpleEditorCanvasScene:setCameraZoom( zoom )
	return self:getCameraComponent():setZoom( zoom )
end


-- --------------------------------------------------------------------
-- function createEditorCanvasScene( env, canvasViewClass )
-- 	local env = env or getfenv( 2 )
-- 	local scn = EditorCanvasScene( env )
-- 	scn:init()
-- 	return scn
-- end

--------------------------------------------------------------------
function createSimpleEditorCanvasScene( env )
	local env = env or getfenv( 2 )
	local scn = SimpleEditorCanvasScene( env )
	scn:init()
	scn:start()
	return scn
end

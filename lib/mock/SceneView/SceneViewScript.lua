require 'mock_edit'

--------------------------------------------------------------------
view = false

function onSceneOpen( scene )
	view = mock_edit.createSceneView( scene, _M )

	view:registerDragFactory( mock_edit.ProtoDragInFactory() )
	view:registerDragFactory( mock_edit.TextureDragInFactory() )
	view:registerDragFactory( mock_edit.DeckDragInFactory() )
	view:registerDragFactory( mock_edit.MSpriteDragInFactory() )

	scene:addEntity( view )
	view:makeCurrent()

	return view
end

function onSceneClose()
	view = false
end


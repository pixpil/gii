--------------------------------------------------------------------
-- scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

scn = mock_edit.EditorCanvasScene( _M, { ['use_game_layer'] = true } )
scn.FLAG_PREVIEW_SCENE = true
scn:init()

preview = mock_edit.createProtoPreview( _M )
scn:addEntity( preview )

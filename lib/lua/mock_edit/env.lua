module 'mock_edit'

--TODO: deprecate this

local editingScene = false
function getEditingScene()
	return editingScene
end

function setEditingScene( scn )
	editingScene = scn
end

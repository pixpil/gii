-- module 'mock_edit'

-- local function onAssetModified( node )
-- 	if node:getType() ~= 'fmod_project' then return end

-- 	local path = node:getNodePath()
-- 	local mockNode = mock.getAssetNode( path )
-- 	if mockNode then mock.updateAssetNode( mockNode, _pyAssetNodeToData( node ) ) end

-- 	for item in pairs( mock.getLoadedDecks() ) do
-- 		if item:getTexture() == path then
-- 			-- print( 'update deck!!', item )
-- 			item:setTexture( path, false )
-- 		end
-- 	end
	
-- end

-- connectSignalFunc( 'asset.modified', onAssetModified )


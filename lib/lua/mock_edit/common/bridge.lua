module 'mock_edit'

--------------------------------------------------------------------
--Asset Sync
--------------------------------------------------------------------
function _pyAssetNodeToData( node )
	return {
			nodePath    = node.nodePath,
			deploy      = node.deployState == true,
			filePath    = node.filePath,
			type        = node.assetType,
			objectFiles = gii.dictToTable( node.objectFiles ),
			properties  = gii.dictToTable( node.properties ),
			dependency  = gii.dictToTable( node.dependency ),
			fileTime    = node.fileTime
		}
end

local function onAssetModified( node ) --node: <py>AssetNode	
	local nodepath = node:getPath()
	mock.releaseAsset( nodepath )
	local mockNode = mock.getAssetNode( nodepath )
	if mockNode then
		local data = _pyAssetNodeToData( node )
		mock.updateAssetNode( mockNode, data )
		emitSignal( 'asset.modified', mockNode )
		if mock.game:isInitialized() then
			mock.getGiiSyncHost():tellConnectedPeers( 'asset.modified', data )
		end
	end
end

local function onAssetRegister( node )
	local nodePath = node:getPath()
	local data = _pyAssetNodeToData( node )
	mock.registerAssetNode( nodePath, data )
	if mock.game:isInitialized() then
		mock.getGiiSyncHost():tellConnectedPeers( 'asset.register', data )
	end
end

local function onAssetUnregister( node )
	local nodePath = node:getPath()
	mock.unregisterAssetNode( nodePath )
	if mock.game:isInitialized() then
		mock.getGiiSyncHost():tellConnectedPeers( 'asset.unregister', nodePath )
	end
end

local function onTextureRebuilt( node )
	local nodepath = node:getPath()
	if mock.game:isInitialized() then
		mock.getGiiSyncHost():tellConnectedPeers( 'texture.rebuild', nodepath )
	end
end

gii.connectPythonSignal( 'asset.imported',   onAssetModified )
gii.connectPythonSignal( 'asset.register',   onAssetRegister )
gii.connectPythonSignal( 'asset.unregister', onAssetUnregister )
gii.connectPythonSignal( 'texture.rebuild',  onTextureRebuilt )

--------------------------------------------------------------------
local function onContextChange( ctx, oldCtx )
	mock.game:setCurrentRenderContext( ctx )
end

gii.addContextChangeListeners( onContextChange )


module 'mock_edit'

local function onTextureRebuilt( node )
	local ntype = node:getType()
	if ntype ~= 'texture' then
		return
	end

	local path = node:getNodePath()
	local asset = mock.getCachedAsset( path )
	if not asset then return end
	if asset.valid then return end
	asset:load()
	gii.emitPythonSignal( 'scene.update' )

end

gii.connectPythonSignal( 'texture.rebuild',   onTextureRebuilt )


module 'mock_edit'

local function onAssetModified( node )
	local ntype = node:getType()
	if ntype ~= 'lut_texture' then
		return
	end
	local path = node:getNodePath()
	if not mock.getLoadedLUTTexture( path ) then return end
	mock.loadAsset( path )
	mock.refreshColorGradingTextures()
	gii.emitPythonSignal( 'scene.update' )
end

connectSignalFunc( 'asset.modified', onAssetModified )


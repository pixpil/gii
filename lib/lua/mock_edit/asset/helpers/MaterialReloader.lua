module 'mock_edit'
local function onAssetModified( node )
	local atype = node:getType()
	if atype == 'material' then
		--TODO
		--TODO
		--TODO
		--TODO
	else
		return
	end
	gii.emitPythonSignal( 'scene.update' )

end

connectSignalFunc( 'asset.modified', onAssetModified )


module 'mock_edit'

local function onAssetModified( node )
	local atype = node:getType()

	if atype == 'tb_scheme' then
		local scheme = node:getCachedAsset()
		if not scheme then
			scheme = node:load()
		else
			scheme:_reload()
		end
		
	elseif atype == 'tb_skin' then
		local skin = node:getCachedAsset()
		-- skin:_reload()
	end
	
	gii.emitPythonSignal( 'scene.update' )

end

connectSignalFunc( 'asset.modified', onAssetModified )


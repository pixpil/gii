module 'mock_edit'
AssetTools = {}

--------------------------------------------------------------------
mock.registerSyncQueryHandler( function( key, context )
		if key == 'asset.remote_source_files' then
			local path = context[ 'path' ]
			local result = {}
			local pyAssetLibrary = gii.app:getAssetLibrary()
			local pyAssetNode = pyAssetLibrary:getAssetNode( path )
			if not pyAssetNode then
				return false
			end
			local files = pyAssetNode:getRemoteSourceFiles()
			if files then files = gii.listToTable( files ) end
			for i, entry in pairs( files ) do
				local url    = entry[ 0 ]
				local target = entry[ 1 ]
				result[ i ] = {
					url = url,
					target = target
				}
			end
			return result
		end
	end,
	'editor'
)

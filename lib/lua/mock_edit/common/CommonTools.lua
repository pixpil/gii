module 'mock_edit'

--replace these functions for the project's need
CommonTools = {}

--------------------------------------------------------------------
function CommonTools.createEmptyEntity( parentEntity, ... )
	return mock.Entity( ... )
end

function CommonTools.createComponent( clas, ... )
	if type( clas ) == 'string' then
		clas = mock.getComponentType( clas )
	end
	assert( clas )
	return clas( ... )
end

mock.registerSyncQueryHandler( function( key, context )
		if key == 'cmd.show_file_os' then
			gii.app:showFileInOS( context['path'] )
		elseif key == 'cmd.open_file_os' then
			gii.app:openFileInOS( context['path'] )
		elseif key == 'cmd.locate_asset_editor' then
			gii.app:getModule( 'asset_browser' ):locateAsset( context[ 'path' ] )
		elseif key == 'cmd.edit_asset_editor' then
			local lib = gii.app:getAssetLibrary()
			local pyAssetNode = lib:getAssetNode( context[ 'path' ] )
			if pyAssetNode then 
				pyAssetNode:edit()
			end
		elseif key == 'cmd.open_file_sublime' then
			gii.app:getModule( 'sublime_remote' ):openFile( 
				context[ 'path' ],
				context[ 'line' ]
			 )
		end
	end,
	'editor'
)


module 'mock_edit'

local SearchView = gii.importPythonModule 'gii.SearchView'

function requestSearchView( option )
	local dict = gii.newPythonDict()
	for k, v in pairs( option ) do
		dict[ k ] = v
	end
	return SearchView.requestSearchView_dict( dict )	
end
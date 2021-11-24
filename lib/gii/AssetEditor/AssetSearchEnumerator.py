from gii.core import *
from gii.SearchView  import requestSearchView, registerSearchEnumerator

##----------------------------------------------------------------##
def assetCreatorSearchEnumerator( typeId, context, option ):
	if not context in [ 'asset_creator' ] : return None
	result = []
	for creator in AssetLibrary.get().assetCreators:
		entry = ( creator, creator.getLabel(), 'asset_creator', None )
		result.append( entry )
	return result

registerSearchEnumerator( assetCreatorSearchEnumerator  )

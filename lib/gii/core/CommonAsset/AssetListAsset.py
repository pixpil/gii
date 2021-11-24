import os.path

from gii.core import AssetManager, AssetLibrary, app, JSONHelper
from gii.core import AssetManager

class AssetListAssetManager( AssetManager ):
	def getName(self):
		return 'asset_manager.asest_list'

	def getMetaType( self ):
		return 'asest_list'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name,ext = os.path.splitext(filepath)
		return ext in ['.asset_list' ]

	def importAsset(self, node, reload = False ):
		node.assetType = 'asset_list'
		node.setObjectFile( 'data', node.getFilePath() )
		return True

AssetListAssetManager().register()

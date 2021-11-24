import os.path

from gii.core import AssetManager, AssetLibrary, app, JSONHelper
from .DataYAMLAsset import DataYAMLAssetManager

class AssetMapAssetManager( DataYAMLAssetManager ):
	def getName(self):
		return 'asset_manager.asset_map'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name, ext = os.path.splitext(filepath)
		return ext in ['.asset_map' ]

	def importAsset(self, node, reload = False ):
		imported = super( AssetMapAssetManager, self ).importAsset( node, reload )
		node.assetType = 'asset_map'
		return imported

AssetMapAssetManager().register()
AssetLibrary.get().setAssetIcon( 'asset_map',  'asset_map' )

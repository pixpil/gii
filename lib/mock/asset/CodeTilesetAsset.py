import os.path
import json

from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper
from .helper.psd2tileset import TilesetProject
from gii.core.CommonAsset.DataYAMLAsset import DataYAMLAssetManager

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class CodeTilesetAssetManager(DataYAMLAssetManager):
	def getName(self):
		return 'asset_manager.code_tileset'
	
	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		if not filepath.endswith( '.code_tileset' ): return False
		return True

	def postDataLoad( self, node, data ):
		tiles = data.get( 'tiles', None )
		if not tiles: return
		id = 0
		for key, value in list(tiles.items()):
			id +=1
			value[ '_id' ] = id

	def importAsset(self, node, reload = False ):
		imported = super( CodeTilesetAssetManager, self ).importAsset( node, reload )
		node.assetType = 'code_tileset'
		return imported

CodeTilesetAssetManager().register()
AssetLibrary.get().setAssetIcon( 'code_tileset',  'cell' )

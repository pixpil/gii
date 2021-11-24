import os.path
from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper
from .helper.psd2tileset import TilesetProject
import json

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class NamedTilesetAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.named_tileset'
	
	def getPriority( self ):
		return 1000

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		if not filepath.endswith( '.ntileset.psd' ): return False
		return True

	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		node.assetType = 'named_tileset_pack'
		#atlas
		atlasFile = node.getCacheFile( 'atlas' )
		node.setObjectFile( 'atlas', atlasFile )
		#define
		defFile = node.getCacheFile( 'def' )
		node.setObjectFile( 'def', defFile )
		
		proj = TilesetProject()
		proj.loadPSD( node.getAbsFilePath() )
		absAtlas, absDef = node.getAbsObjectFile( 'atlas' ), node.getAbsObjectFile( 'def' )
		proj.save( absAtlas, absDef )
		#TODO: let texture library handle atlas
		pack = JSONHelper.tryLoadJSON( absDef )
		for item in pack[ 'themes' ]:
			node.affirmChildNode( item[ 'name' ], 'named_tileset', manager = self )
		return True

NamedTilesetAssetManager().register()

AssetLibrary.get().setAssetIcon( 'named_tileset_pack',  'pack' )
AssetLibrary.get().setAssetIcon( 'named_tileset',  'cell' )

import os.path
from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper
# from helper.psd2deckpack import DeckPackProject

from .helper.PSDLayerExtractor import PSDLayerExtractor
import json

from mock import _MOCK, _MOCK_EDIT, isMockInstance, getMockClassName


class PSDTexturePackAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.texpack_psd'
	
	def getPriority( self ):
		return 1000

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		if not filepath.endswith( '.textures.psd' ): return False
		return True

	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		node.setBundle()

		node.assetType = 'texture_pack'
		node.groupType = 'package'
		
		output = node.getCacheFile( 'export', is_dir = True )
		extractor = PSDLayerExtractor()
		result = extractor.extract( node.getAbsFilePath(), output )

		#import
		for item in result:
			name, absPath, filename = item
			texNode = node.affirmChildNode( name, 'texture', manager = 'asset_manager.texture' )
			texNode.setWorkspaceData( 'source', absPath )
			app.getModule( 'texture_library' ).scheduleImport( texNode )

		return True

##----------------------------------------------------------------##
PSDTexturePackAssetManager().register()

AssetLibrary.get().setAssetIcon( 'texture_pack',  'pack' )

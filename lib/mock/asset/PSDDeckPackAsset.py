import os.path
from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper
# from helper.psd2deckpack import DeckPackProject

from .helper.PSDDeckPackProject import PSDDeckPackProject
from .helper import PSDDeckMTileset
from .helper import PSDDeckMQuad
from .helper import PSDDeckQuads

from .TextureConverter import convertTextureFormat

import json

from mock import _MOCK, _MOCK_EDIT, isMockInstance, getMockClassName


def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

#----------------------------------------------------------------
class DeckPSDAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.deckpack_psd'
	
	def getPriority( self ):
		return 1000

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		if not filepath.endswith( '.decks.psd' ): return False
		return True

	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		node.assetType = 'deck_pack'
		node.groupType = 'package'
		
		output = node.getCacheFile( 'export', is_dir = True )
		node.setObjectFile( 'export', output )

		proj = PSDDeckPackProject()
		proj.setDefaultProcessor( 'mquad' )

		proj.loadPSD( node.getAbsFilePath() )
		proj.save( output+'/', 'decks', (4096,4096) )

		#import
		jsonPath = output+'/decks.json'
		pack = JSONHelper.tryLoadJSON( jsonPath )
		for item in pack[ 'decks' ]:
			name = item['name']
			deckType = item['type']
			node.affirmChildNode( item[ 'name' ], deckType, manager = self )

		return True

	def deployAsset( self, assetNode, context ):
		if not assetNode.getType() in ['deck_pack', 'deck_pack_raw']: return
		info = context.getAssetDeployInfo( assetNode )
		# if info and info.get( 'mtime', 0 ) == assetNode.getFileTime(): return
		packedPath = context.addAssetObjectFile( assetNode, 'export' )
		if packedPath:
			#convert texture format
			absPackedPath = context.getAbsPath( packedPath )
			for name in os.listdir( absPackedPath ):
				n, ext = os.path.splitext( name )
				if ext == '.png':
					src = absPackedPath + '/' + name
					dst = absPackedPath + '/' + n + '.hmg'
					convertTextureFormat( None, 'auto', src, dst, reason = 'deploy' )
					os.remove( src )

	def hasAssetThumbnail( self, assetNode ):
		if assetNode.groupType == None and assetNode.getType().startswith( 'deck2d.' ):
			return True
		else:
			return False

	def buildAssetThumbnail( self, assetNode, targetPath, size ):
		nodePath = assetNode.getPath()
		w, h = size
		if _MOCK_EDIT.buildDeckThumbnail( nodePath, targetPath, w, h ):
			return True
		else:
			return False

DeckPSDAssetManager().register()

#----------------------------------------------------------------
class DeckPackFolderAssetManager(DeckPSDAssetManager):
	def getName(self):
		return 'asset_manager.deckpack_folder'
	
	def acceptAssetFile(self, filepath):
		if not os.path.isdir(filepath): return False		
		if not filepath.endswith( '.deckpack' ): return False
		return True

	def importAsset(self, node, reload = False ):
		node.setBundle()
		node.assetType = 'deck_pack_raw'
		node.groupType = 'package'
		
		node.setObjectFile( 'export', node.getFilePath() )
		#import
		jsonPath = node.getFilePath()+'/decks.json'
		pack = JSONHelper.tryLoadJSON( jsonPath )
		for item in pack[ 'decks' ]:
			name = item['name']
			deckType = item['type']
			node.affirmChildNode( item[ 'name' ], deckType, manager = self )
		return True

DeckPackFolderAssetManager().register()

#----------------------------------------------------------------
AssetLibrary.get().setAssetIcon( 'deck_pack',           'pack' )
AssetLibrary.get().setAssetIcon( 'deck_pack_raw',       'pack' )
AssetLibrary.get().setAssetIcon( 'deck2d.quads',        'deck_quad_array' )
AssetLibrary.get().setAssetIcon( 'deck2d.mquad',        'deck_mquad' )
AssetLibrary.get().setAssetIcon( 'deck2d.mtileset',     'deck_mtileset' )

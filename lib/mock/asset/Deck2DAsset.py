import os.path
from gii.core import *
from mock import _MOCK, _MOCK_EDIT, isMockInstance, getMockClassName
import json

##----------------------------------------------------------------##
class Deck2DAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.deck2d'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ '.deck2d' ]: return False
		return _MOCK.checkSerializationFile( filePath, 'mock.Deck2DPack' )
		
	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		node.assetType = 'deck2d'
		node.groupType = 'package'
		
		pack = _MOCK.deserializeFromFile( None, node.getAbsFilePath() )
		if not pack:
			return False

		for item in list(pack.decks.values()):
			deckType = 'deck2d.' + item.type
			name  =  item.name
			childNode = node.affirmChildNode( name, deckType, manager = self )
			texture = item.texturePath
			if texture:
				childNode.addDependency( 'texture', texture )

		node.setObjectFile( 'def', node.getFilePath() )
		return True

	def editAsset(self, node):	
		editor = app.getModule( 'deck2d_editor' )
		if not editor: 
			return alertMessage( 'Editor not load', 'Deck2D Editor not found!' )
		if not node.isType( 'deck2d' ):
			editor.openAsset( node.getParent(), node )			
		else:
			editor.openAsset( node )

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


##----------------------------------------------------------------##
class Deck2DCreator(AssetCreator):
	def getAssetType( self ):
		return 'deck2d'

	def getLabel( self ):
		return 'Deck2D Pack'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.deck2d'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
	
		_MOCK.createEmptySerialization( fullpath, 'mock.Deck2DPack' )
		return nodepath
		
##----------------------------------------------------------------##
Deck2DAssetManager().register()
Deck2DCreator().register()

AssetLibrary.get().setAssetIcon( 'deck2d',              'pack' )
AssetLibrary.get().setAssetIcon( 'deck2d.quad',         'deck_quad' )
AssetLibrary.get().setAssetIcon( 'deck2d.tileset',      'deck_tileset' )
AssetLibrary.get().setAssetIcon( 'deck2d.stretchpatch', 'deck_patch' )
AssetLibrary.get().setAssetIcon( 'deck2d.quad_array',   'deck_quad_array' )
AssetLibrary.get().setAssetIcon( 'deck2d.polygon',      'deck_polygon' )

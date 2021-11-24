import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *
from mock import _MOCK

_MATERIAL_EXT  = '.material'
_MATERIAL_TYPE = 'material'

##----------------------------------------------------------------##
##----------------------------------------------------------------##
class RenderMaterialAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.' + _MATERIAL_TYPE

	def getMetaType( self ):
		return 'serializable'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ _MATERIAL_EXT ]: return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = _MATERIAL_TYPE
		node.setObjectFile( 'def', node.getFilePath() )
		return True

	def editAsset(self, node):	
		editor = app.getModule( 'serializable_editor' )
		if not editor: 
			return alertMessage( 'Editor not load', 'Asset Editor not found!' )
		else:
			editor.openAsset( node )
			
##----------------------------------------------------------------##
class RenderMaterialAssetCreator(AssetCreator):
	def getAssetType( self ):
		return _MATERIAL_TYPE

	def getLabel( self ):
		return 'Render Material'

	def createAsset( self, name, contextNode, assetType ):
		filename = name + _MATERIAL_EXT
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		
		_MOCK.createEmptySerialization( fullpath, 'mock.RenderMaterial' )
		return nodepath

##----------------------------------------------------------------##
RenderMaterialAssetManager().register()
RenderMaterialAssetCreator().register()

AssetLibrary.get().setAssetIcon( 'material',  'material' )

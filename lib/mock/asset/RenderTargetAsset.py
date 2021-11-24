import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *
from mock import _MOCK

##----------------------------------------------------------------##
class RenderTargetAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.render_target'

	def getMetaType( self ):
		return 'texture'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ '.render_target' ]: return False
		return _MOCK.checkSerializationFile( filePath, 'mock.RenderTargetTexture' )

	def importAsset( self, node, reload = False ):
		node.assetType = 'render_target'		
		node.setObjectFile( 'def', node.getFilePath() )
		return True

##----------------------------------------------------------------##
class RenderTargetCreator(AssetCreator):
	def getAssetType( self ):
		return 'render_target'

	def getLabel( self ):
		return 'Render Target Texture'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.render_target'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		
		_MOCK.createEmptySerialization( fullpath, 'mock.RenderTargetTexture' )
		return nodepath


##----------------------------------------------------------------##
RenderTargetAssetManager().register()
RenderTargetCreator().register()

AssetLibrary.get().setAssetIcon( 'render_target',  'framebuffer' )

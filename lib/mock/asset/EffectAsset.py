import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *
from mock import _MOCK

from gii.qt.dialogs   import requestString, alertMessage, requestConfirm

##----------------------------------------------------------------##
class EffectAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.effect'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		return ext == '.effect'

	def importAsset( self, node, reload = False ):
		fileName, ext = os.path.splitext( node.getFilePath() )
		node.assetType = 'effect'
		node.setObjectFile( 'def', node.getFilePath() )
		return True

	def editAsset(self, node):
		editor = app.getModule( 'effect_editor' )
		if not editor: 
			return alertMessage( 'Editor not load', 'Effect Editor not found!' )
		editor.openAsset( node )		


##----------------------------------------------------------------##
class EffectAssetCreator( AssetCreator ):
	def getAssetType( self ):
		return 'effect'

	def getLabel( self ):
		return 'Effect Config'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.effect'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		
		_MOCK.createEmptySerialization( fullpath, 'mock.EffectConfig' )
		return nodepath


##----------------------------------------------------------------##
EffectAssetManager().register()
EffectAssetCreator().register()

AssetLibrary.get().setAssetIcon( 'effect',  'fx' )

import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *
from mock import _MOCK

from gii.qt.dialogs   import requestString, alertMessage, requestConfirm



##----------------------------------------------------------------##
class MovieAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.movie'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		return ext in [ '.ogv', '.mp4', '.webm' ]

	def getDefaultAssetDeployConfig( self, node ):
		return dict(
			package  = 'movie',
			compress = False
		)

	def importAsset( self, node, reload = False ):
		fileName, ext = os.path.splitext( node.getFilePath() )
		imported = False
		movieFormat = None
		if ext == '.ogv': #Try import as theora
			movieFormat = 'theora'
			#TODO: validation?
			imported = True
		elif ext == '.mp4':
			movieFormat = 'mp4'
			imported = True
		elif ext == '.webm':
			movieFormat = 'WebM'
			imported = True

		if not imported: return False
		node.assetType = 'movie'
		node.setProperty( 'format', movieFormat )
		node.setObjectFile( 'data', node.getFilePath() )
		return True


##----------------------------------------------------------------##
MovieAssetManager().register()

AssetLibrary.get().setAssetIcon( 'movie',  'clip' )

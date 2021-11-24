import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *
from mock import _MOCK

##----------------------------------------------------------------##
class ShaderAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.shader'

	def getMetaType( self ):
		return 'script'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ '.shader' ]: return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = 'shader'		
		node.setObjectFile( 'def', node.getFilePath() )
		return True

##----------------------------------------------------------------##
ShaderAssetManager().register()
AssetLibrary.get().setAssetIcon( 'shader',  'shader' )

import os.path
import logging
import subprocess
import shutil
import json
from util.YAMLHelper import *

from gii.core import *
from mock import _MOCK

##----------------------------------------------------------------##
class MultiTextureAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.multi_texture'

	def getMetaType( self ):
		return 'script'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ '.multi_texture' ]: return False
		return True

	def importAsset(self, node, reload = False ):
		try:
			fp = open( node.getAbsFilePath(), 'r' )
			# text = fp.read()
			data = orderedLoadYaml( fp )
		except Exception as e:
			logging.warn( 'failed to parse yaml:%s' % node.getPath() )
			print(e)
			return False

		cachePath = node.getCacheFile( 'data' )
		if not JSONHelper.trySaveJSON( data, cachePath ):
			logging.warn( 'failed saving yaml data to json: %s' % cachePath )
			return False

		node.assetType = 'multi_texture'
		node.setObjectFile( 'data', cachePath )
		return True


##----------------------------------------------------------------##
MultiTextureAssetManager().register()

AssetLibrary.get().setAssetIcon( 'multi_texture',  'multi_texture' )

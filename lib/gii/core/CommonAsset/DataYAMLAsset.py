import os.path
import logging
import json

from gii.core import AssetManager, AssetLibrary, app, JSONHelper
from util.YAMLHelper import *
	
##----------------------------------------------------------------##
class DataYAMLAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.data_yaml'
		
	def getMetaType( self ):
		return 'script'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name, ext = os.path.splitext(filepath)
		if not ext in ['.yaml']: return False		
		return True

	def postDataLoad( self, node, data ):
		return

	def importAsset(self, node, reload = False ):
		try:
			with open( node.getAbsFilePath(), 'r', encoding = 'utf-8' ) as fp:
				# text = fp.read()
				data = orderedLoadYaml( fp )
		except Exception as e:
			logging.warn( 'failed to parse yaml:%s' % node.getPath() )
			print( e )
			return False

		self.postDataLoad( node, data )

		cachePath = node.getCacheFile( 'data' )
		if not JSONHelper.trySaveJSON( data, cachePath, 'yaml2json', sort_keys = False ):
			logging.warn( 'failed saving yaml data to json: %s' % cachePath )
			return False

		node.assetType = 'data_yaml'
		node.setObjectFile( 'data', cachePath )
		return True

DataYAMLAssetManager().register()
AssetLibrary.get().setAssetIcon( 'data_yaml', 'data' )

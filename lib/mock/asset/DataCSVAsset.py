import os.path
import logging
import json
import csv

from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper
from .helper.CSVTool import *


##----------------------------------------------------------------##
class DataCSVAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.data_csv'
		
	def getMetaType( self ):
		return 'script'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name, ext = os.path.splitext(filepath)
		if not ext in ['.csv']: return False		
		return True

	def importAsset(self, node, reload = False ):
		data = {}
		path = node.getFilePath()
		if path.endswith( '.dict.csv' ):
			try:
				data = loadCSVAsDict( node.getAbsFilePath() )
			except Exception as e:
				logging.warn( 'Failed importing dict csv:' + node.getPath() )
				return False

		elif path.endswith( '.list.csv' ):
			try:
				data = loadCSVAsList( node.getAbsFilePath() )
			except Exception as e:
				logging.warn( 'Failed importing list csv:' + node.getPath() )
				return False

		else:
			try:
				data = loadPlainCSV( node.getAbsFilePath() )
			except Exception as e:
				logging.warn( 'Failed importing plain csv:' + node.getPath() )
				return False

		cachePath = node.getCacheFile( 'data' )
		if not JSONHelper.trySaveJSON( data, cachePath ):
			logging.warn( 'failed saving csv data to json: %s' % cachePath )
			return False

		node.assetType = 'data_csv'
		node.setObjectFile( 'data', cachePath )
		return True

DataCSVAssetManager().register()
AssetLibrary.get().setAssetIcon( 'data_csv', 'data' )


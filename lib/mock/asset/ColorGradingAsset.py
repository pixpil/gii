import os.path
from gii.core import *
from mock import _MOCK
import json

##----------------------------------------------------------------##
class ColorGradingAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.color_grading'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ '.color_grading' ]: return False
		return _MOCK.checkSerializationFile( filePath, 'mock.ColorGradingConfig' )
		
	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		node.assetType = 'color_grading'
		node.groupType = 'package'
		
		pack = _MOCK.deserializeFromFile( None, node.getAbsFilePath() )
		if not pack:
			return False

		node.setObjectFile( 'data', node.getFilePath() )
		return True


##----------------------------------------------------------------##
class ColorGradingCreator(AssetCreator):
	def getAssetType( self ):
		return 'color_grading'

	def getLabel( self ):
		return 'ColorGrading Pack'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.color_grading'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
	
		_MOCK.createEmptySerialization( fullpath, 'mock.ColorGradingConfig' )
		return nodepath
		
##----------------------------------------------------------------##
ColorGradingAssetManager().register()
ColorGradingCreator().register()

AssetLibrary.get().setAssetIcon( 'color_grading',              'color' )

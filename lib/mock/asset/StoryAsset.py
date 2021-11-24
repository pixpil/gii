import os.path
import subprocess
import shutil

from gii.core import *

from .tools.ml2story import StoryGraphParser

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
	
##----------------------------------------------------------------##
class StoryGraphAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.story_graph'

	def acceptAssetFile( self, filePath ):
		if os.path.isdir(filePath): return False		
		if not filePath.endswith( '.story.graphml' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = 'story_graph'
		node.setObjectFile( 'def', node.getCacheFile( 'def' ) )
		parser = StoryGraphParser()
		if parser.parse( node.getAbsFilePath() ):
			outputFile = node.getAbsObjectFile( 'def' )
			parser.saveToJson( outputFile )
			return True
		else:
			return False

StoryGraphAssetManager().register()
AssetLibrary.get().setAssetIcon( 'story_graph',  'story' )

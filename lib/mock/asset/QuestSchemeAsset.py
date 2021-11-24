import os.path
import subprocess
import shutil

from gii.core import *

from .tools.ML2QuestScheme import QuestSchemeParser

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
	
##----------------------------------------------------------------##
class ScenePortalGraphAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.quest_scheme'

	def acceptAssetFile( self, filePath ):
		if os.path.isdir(filePath): return False		
		if not filePath.endswith( '.quest.graphml' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = 'quest_scheme'
		node.setObjectFile( 'def', node.getCacheFile( 'def' ) )
		parser = QuestSchemeParser()
		if parser.parse( node.getAbsFilePath() ):
			outputFile = node.getAbsObjectFile( 'def' )
			parser.saveToJson( outputFile )
			return True
		else:
			return False

	
##----------------------------------------------------------------##
class ScenePortalGraphCreator(AssetCreator):
	def getAssetType( self ):
		return 'quest_scheme'

	def getLabel( self ):
		return 'QuestScheme'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.quest.graphml'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		shutil.copy( _getModulePath( 'template/empty.quest.graphml' ), fullpath )
		return nodepath


ScenePortalGraphAssetManager().register()
ScenePortalGraphCreator().register()
AssetLibrary.get().setAssetIcon( 'quest_scheme',  'portal_graph' )

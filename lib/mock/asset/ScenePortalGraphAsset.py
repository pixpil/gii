import os.path
import subprocess
import shutil

from gii.core import *

from .tools.ML2PortalGraph import PortalGraphParser

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
	
##----------------------------------------------------------------##
class ScenePortalGraphAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.scene_portal_graph'

	def acceptAssetFile( self, filePath ):
		if os.path.isdir(filePath): return False		
		if not filePath.endswith( '.portal.graphml' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = 'scene_portal_graph'
		node.setObjectFile( 'def', node.getCacheFile( 'def' ) )
		parser = PortalGraphParser()
		if parser.parse( node.getAbsFilePath() ):
			outputFile = node.getAbsObjectFile( 'def' )
			parser.saveToJson( outputFile )
			return True
		else:
			return False

	
##----------------------------------------------------------------##
class ScenePortalGraphCreator(AssetCreator):
	def getAssetType( self ):
		return 'scene_portal_graph'

	def getLabel( self ):
		return 'PortalGraph'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.portal.graphml'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		shutil.copy( _getModulePath( 'template/empty.portal.graphml' ), fullpath )
		return nodepath


ScenePortalGraphAssetManager().register()
ScenePortalGraphCreator().register()
AssetLibrary.get().setAssetIcon( 'scene_portal_graph',  'portal_graph' )

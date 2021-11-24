import os.path
import subprocess
import shutil

from gii.core import *

from .tools.ml2fsm import convertGraphMLToFSM

from gii.moai.ScriptHelpers import compileLuaJIT


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
	
##----------------------------------------------------------------##
class FSMSchemeAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.fsm_scheme'

	def acceptAssetFile( self, filePath ):
		if not os.path.isfile(filePath): return False		
		if not filePath.endswith( '.fsm.graphml' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.setObjectFile( 'def', node.getCacheFile( 'def' ) )
		convertGraphMLToFSM(
			node.getAbsFilePath(), #input file
			node.getAbsObjectFile( 'def' ) #output file
		)
		node.assetType = 'fsm_scheme'
		return True

	# def deployAsset( self, assetNode, context ):
	# 	super( FSMSchemeAssetManager, self ).deployAsset( assetNode, context )
	# 	luaversion = context.getMeta( 'lua_version', 'lua' )

	
##----------------------------------------------------------------##
class FSMSchemeCreator(AssetCreator):
	def getAssetType( self ):
		return 'fsm_scheme'

	def getLabel( self ):
		return 'FSMScheme'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.fsm.graphml'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		shutil.copy( _getModulePath( 'template/empty.fsm.graphml' ), fullpath )
		return nodepath


FSMSchemeAssetManager().register()
FSMSchemeCreator().register()
AssetLibrary.get().setAssetIcon( 'fsm_scheme',    'scheme' )

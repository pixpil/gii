import os.path
import subprocess
import shutil

from gii.core import *
from gii.qt.dialogs   import requestString, alertMessage
from util.SQScript import SQScriptCompiler
from mock import _MOCK



##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
	

EMPTY_SQ_SCRIPT = '''//sqscript
//File: %s
!start

'''

##----------------------------------------------------------------##
class SQScriptAssetCreator(AssetCreator):
	def getAssetType( self ):
		return 'sq_script'

	def getLabel( self ):
		return 'SQScript'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.sq'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		if os.path.exists(fullpath):
			raise Exception('File already exist:%s'%fullpath)
		fp = open(fullpath,'w')
		fp.write( EMPTY_SQ_SCRIPT % name )
		fp.close()
		return nodepath


##----------------------------------------------------------------##
class SQScriptAssetManager(AssetManager):
	def getMetaType(self):
		return 'script'
		
	def getName(self):
		return 'asset_manager.sq_script'

	def acceptAssetFile( self, filePath ):
		if os.path.isdir(filePath): return False		
		if not filePath.endswith( '.sq' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = 'sq_script'
		node.setObjectFile( 'data', node.getCacheFile( 'data' ) )
		node.setObjectFile( 'packed_data', node.getCacheFile( 'packed_data' ) )
		compiler = SQScriptCompiler()
		try:
			root = compiler.parseFile( node.getAbsFilePath(), node.getPath() )
		except Exception as e:
			logging.error( e )
			return False
		
		data = root.toJSON()
		JSONHelper.trySaveJSON( data, node.getAbsObjectFile( 'data' ) )
		JSONHelper.saveMsgPack( data, node.getAbsObjectFile( 'packed_data' ) )
		return True

	# def editAsset(self, node):	
	# 	editor = app.getModule( 'sq_script_editor' )
	# 	if not editor: 
	# 		return alertMessage( 'Editor not load', 'Asset Editor not found!' )
	# 	else:
	# 		editor.openAsset( node )

SQScriptAssetManager().register()
SQScriptAssetCreator().register()
AssetLibrary.get().setAssetIcon( 'sq_script',  'story' )

##----------------------------------------------------------------##

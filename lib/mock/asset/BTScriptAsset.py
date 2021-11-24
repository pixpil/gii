import os.path
import subprocess
import shutil

from gii.core import *
from mock import _MOCK


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
	
##----------------------------------------------------------------##
class BTScriptAssetManager(AssetManager):
	def getMetaType(self):
		return 'script'
		
	def getName(self):
		return 'asset_manager.bt_script'

	def acceptAssetFile( self, filePath ):
		if not os.path.isfile(filePath): return False		
		if not filePath.endswith( '.bt_script' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.setObjectFile( 'def', node.getFilePath() )
		node.assetType = 'bt_script'
		#validate
		try:
			_MOCK.parseBTScriptFile( node.getFilePath() )
		except Exception as e:
			pass
		return True
	
		
##----------------------------------------------------------------##
class BTScriptCreator(AssetCreator):
	def getAssetType( self ):
		return 'bt_script'

	def getLabel( self ):
		return 'BTScript'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.bt_script'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		if os.path.exists(fullpath):
			raise Exception('File already exist:%s'%fullpath)
		fp = open(fullpath,'w')
		fp.write( '+ root\n\t@action\n' )
		fp.close()
		return nodepath


##----------------------------------------------------------------##
BTScriptCreator().register()
BTScriptAssetManager().register()
AssetLibrary.get().setAssetIcon( 'bt_script',  'scheme' )

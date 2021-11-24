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
class ComScriptAssetManager(AssetManager):
	def getMetaType(self):
		return 'script'
		
	def getName(self):
		return 'asset_manager.com_script'

	def acceptAssetFile( self, filePath ):
		if not os.path.isfile(filePath): return False		
		if not filePath.endswith( '.clua' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.setObjectFile( 'script', node.getFilePath() )
		node.assetType = 'com_script'
		return True


##----------------------------------------------------------------##
EMPTY_SCRIPT = '''
----------------------------------------------------------------
-- Component Script: %s
-- vars: self, entity, data
-- use MODEL{ Field ... } to create model for data object
----------------------------------------------------------------

-- function onThread()
-- end

-- function onMsg( msg, data )
-- end

-- function onUpdate( dt )
-- end

'''
##----------------------------------------------------------------##
class ComScriptCreator( AssetCreator ):
	def getAssetType( self ):
		return 'com_script'

	def getLabel( self ):
		return 'ComScript(.clua)'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.clua'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		if os.path.exists( fullpath ):
			raise Exception( 'File already exist:%s' % fullpath )
		fp = open( fullpath, 'w' )
		fp.write( EMPTY_SCRIPT )
		fp.close()
		return nodepath


##----------------------------------------------------------------##
ComScriptCreator().register()
ComScriptAssetManager().register()
AssetLibrary.get().setAssetIcon( 'com_script',  'com_script' )

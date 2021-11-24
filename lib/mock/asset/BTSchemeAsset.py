import os.path
import subprocess
import shutil

from gii.core import *


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
	
##----------------------------------------------------------------##
class BTSchemeAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.bt_scheme'

	def acceptAssetFile( self, filePath ):
		if not os.path.isfile(filePath): return False		
		if not filePath.endswith( '.bt.mm' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.setObjectFile( 'def', node.getCacheFile( 'def' ) )
		arglist = [
			'lua', 
			_getModulePath( 'tools/mm2bt.lua' ),
			node.getAbsFilePath(), #input file
			node.getAbsObjectFile( 'def' ) #output file
		 ]
		subprocess.call(arglist)
		node.assetType = 'bt_scheme'
		return True
	
# ##----------------------------------------------------------------##
# class BTSchemeCreator(AssetCreator):
# 	def getAssetType( self ):
# 		return 'bt_scheme'

# 	def getLabel( self ):
# 		return 'BTScheme'

# 	def createAsset( self, name, contextNode, assetType ):
# 		ext = '.bt_scheme'
# 		filename = name + ext
# 		if contextNode.isType('folder'):
# 			nodepath = contextNode.getChildPath( filename )
# 		else:
# 			nodepath = contextNode.getSiblingPath( filename )

# 		fullpath = AssetLibrary.get().getAbsPath( nodepath )
# 		data={
# 			'_assetType' : 'bt_scheme', #checksum
# 			'map'     :{},
# 			'entities':[]
# 		}
# 		if os.path.exists(fullpath):
# 			raise Exception('File already exist:%s'%fullpath)
# 		fp = open(fullpath,'w')
# 		json.dump( data, fp, sort_keys=True, indent=2 )
# 		fp.close()
# 		return nodepath

# ##----------------------------------------------------------------##
# BTSchemeCreator().register()

BTSchemeAssetManager().register()
AssetLibrary.get().setAssetIcon( 'bt_scheme',  'scheme' )

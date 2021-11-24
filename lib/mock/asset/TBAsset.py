import os.path
import subprocess
import shutil

from gii.core import *

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
	
##----------------------------------------------------------------##
class TBSkinAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.tb_skin'

	def acceptAssetFile( self, filePath ):
		if not os.path.isdir(filePath): return False		
		if not filePath.endswith( '.tb_skin' ): return False
		return True

	def importAsset( self, node, reload = False ):
		if not node.assetType in [ 'folder' ] : return True
		node.assetType = 'tb_skin'
		node.setBundle()
		output = node.getCacheFile( 'export', is_dir = True )
		node.setObjectFile( 'export', output )
		return True

	
##----------------------------------------------------------------##
class TBSchemeAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.tb_scheme'

	def acceptAssetFile( self, filePath ):
		if not os.path.isfile(filePath): return False		
		if not filePath.endswith( '.tb_scheme' ): return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = 'tb_scheme'
		node.setObjectFile( 'data', node.getFilePath() )
		return True
	
# ##----------------------------------------------------------------##
# class TBSkinCreator(AssetCreator):
# 	def getAssetType( self ):
# 		return 'fsm_scheme'

# 	def getLabel( self ):
# 		return 'TBSkin'

# 	def createAsset( self, name, contextNode, assetType ):
# 		ext = '.fsm_scheme'
# 		filename = name + ext
# 		if contextNode.isType('folder'):
# 			nodepath = contextNode.getChildPath( filename )
# 		else:
# 			nodepath = contextNode.getSiblingPath( filename )

# 		fullpath = AssetLibrary.get().getAbsPath( nodepath )
# 		data={
# 			'_assetType' : 'fsm_scheme', #checksum
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
# TBSkinCreator().register()

TBSkinAssetManager().register()
TBSchemeAssetManager().register()

AssetLibrary.get().setAssetIcon( 'tb_skin', 'guistyle' )
AssetLibrary.get().setAssetIcon( 'tb_scheme', 'guischeme' )

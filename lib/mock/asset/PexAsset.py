import os.path
from gii.core import AssetManager, AssetLibrary, getProjectPath, app

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class PexAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.pex'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name, ext = os.path.splitext(filepath)
		if not ext in ['.pex']: return False
		return True

	def importAsset(self, node, reload = False ):
		node.assetType = 'particle_pex'
		node.setObjectFile( 'def', node.getFilePath() )
		return True


PexAssetManager().register()

AssetLibrary.get().setAssetIcon( 'particle_pex', 'pex' )


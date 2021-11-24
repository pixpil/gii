import os.path

from gii.core import AssetManager

class RawDataAssetManager( AssetManager ):
	def getName(self):
		return 'asset_manager.rawdata'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name,ext = os.path.splitext(filepath)
		return ext in ['.raw']

	def importAsset(self, node, reload = False ):
		node.assetType='raw'
		node.setObjectFile( 'data', node.getFilePath() )
		return True

RawDataAssetManager().register()

import os.path

from gii.core import AssetManager

class TextAssetManager( AssetManager ):
	def getName(self):
		return 'asset_manager.image'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name,ext = os.path.splitext(filepath)
		return ext in [ '.png','.psd','.jpg','.bmp','.jpeg' ]

	def importAsset(self, node, option=None):
		node.assetType = 'image'
		return True

TextAssetManager().register()


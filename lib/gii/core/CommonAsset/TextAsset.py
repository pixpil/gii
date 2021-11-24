import os.path

from gii.core import AssetManager

class TextAssetManager( AssetManager ):
	def getName(self):
		return 'asset_manager.text'

	def getMetaType( self ):
		return 'text'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name,ext = os.path.splitext(filepath)
		return ext in ['.txt','.html','.htm','.xml','.json'] or name in ('README','TODO')

	def importAsset(self, node, reload = False ):
		node.assetType='text'
		return True


TextAssetManager().register()

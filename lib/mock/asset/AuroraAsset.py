import os.path
from gii.core import AssetManager, AssetLibrary, getProjectPath, app

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class AuroraSpriteAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.aurora_sprite'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name, ext = os.path.splitext(filepath)
		if not ext in ['.sprite']: return False
		
		try:
			f = open(filepath)
			line=f.readline()
			f.close()
			if 'saved by AuroraGT' in line:
				return True
		except e:
			pass
		return False

	def importAsset(self, node, reload = False ):
		node.assetType = 'aurora_sprite'
		scriptPath     = _getModulePath( 'AuroraSpriteImporter.lua' )
		importer       = app.getModule('moai').loadLuaDelegate( scriptPath )

		#TODO: need convert PNG		
		defFile = node.getCacheFile('def')
		
		result = importer.call(
			'convertAuroraSprite', 
			node.getAbsFilePath(),
			getProjectPath( defFile )
			)

		node.setObjectFile( 'def', defFile )
		
		#add depedency
		#TODO: ADD texture dependency

		#add child nodes
		#_frames
		node.createChildNode( 'frames', 'quadlists', manager = self )
		#anim clips
		# print(result, result.animations)
		# #TODO:
		# for key, ani in result.animations.items():
		# 	node.createChildNode( ani.name, 'animclip', manager = self )

		return True

AuroraSpriteAssetManager().register()

AssetLibrary.get().setAssetIcon( 'animclip',      'clip' )
AssetLibrary.get().setAssetIcon( 'quadlists',     'cell' )
AssetLibrary.get().setAssetIcon( 'aurora_sprite', 'clip' )

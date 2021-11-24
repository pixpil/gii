import os.path
from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper
from .helper.MSpriteProject import MSpriteProject
import json

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class MSpriteAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.msprite'

	def acceptAssetFile(self, filepath):
		if not os.path.isdir(filepath): return False		
		if not filepath.endswith( '.msprite' ): return False
		return True

	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		node.assetType = 'msprite'
		node.groupType = None
		node.setBundle()

		#atlas
		atlasFile = node.getCacheFile( 'atlas' )
		# node.setObjectFile( 'atlas', atlasFile )
		
		#define
		defFile = node.getCacheFile( 'def' )
		node.setObjectFile( 'def', defFile )

		packedDefFile = node.getCacheFile( 'packed_def' )
		node.setObjectFile( 'packed_def', packedDefFile )

		proj = MSpriteProject()
		#traverse path
		filePath = node.getFilePath()
		nodePath = node.getNodePath()
		proj.loadFolder( node.getAbsFilePath() )

		#TODO: let texture library handle atlas
		absAtlas = AssetLibrary.get().getAbsProjectPath( atlasFile )
		absDef = AssetLibrary.get().getAbsProjectPath( defFile )
		absPackDef = AssetLibrary.get().getAbsProjectPath( packedDefFile )
		data = proj.save( absAtlas, absDef )
		JSONHelper.saveMsgPack( data, absPackDef )


		atlasNode = node.affirmChildNode( node.getBaseName() + '_texture', 'texture', manager = 'asset_manager.texture' )
		atlasNode.setWorkspaceData( 'source', atlasFile )
		app.getModule( 'texture_library' ).scheduleImport( atlasNode )

		if node.getMetaData( 'build_sub_deck', False ):
			if data:
				for animIdx, animData in data[ 'anims' ].items():
					print(( 'sub node', animData[ 'name' ] ))
					deprecated = animData.get( 'deprecated', False )					
					subNode = node.affirmChildNode( animData[ 'name' ], 'deck2d.msprite_seq', manager = self )
					subNode.setInternalDeprecated( deprecated )
		
		return True

MSpriteAssetManager().register()

AssetLibrary.get().setAssetIcon( 'animclip',   'clip' )
AssetLibrary.get().setAssetIcon( 'quadlists',  'cell' )
AssetLibrary.get().setAssetIcon( 'msprite',    'clip' )
AssetLibrary.get().setAssetIcon( 'deck2d.msprite_seq',  'cell' )

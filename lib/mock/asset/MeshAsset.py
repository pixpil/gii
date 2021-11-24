import os.path
from gii.core import AssetManager, AssetLibrary, getProjectPath, app
from gii.core import AssetManager
import pyassimp
import json
from PIL import Image

MESH_ENABLED = True

class MeshAssetManager( AssetManager ):
	def getName(self):
		return 'asset_manager.mesh'

	def getMetaType( self ):
		return 'mesh'
		
	def acceptAssetFile(self, filepath):
		if not MESH_ENABLED: return False

		if not os.path.isdir(filepath): return False
		if not filepath.endswith( '.mesh' ): return False

		# print("is mesh file")
		return True
		# if not os.path.isfile(filepath): return False		
		# name,ext = os.path.splitext(filepath)
		# return ext in [ '.3ds','.blend','.fbx','.obj' ]

	def importAsset(self, node, reload = False ):
		if not MESH_ENABLED: return False
		
		if not node.assetType in [ 'folder', 'mesh' ] : return True
		node.assetType = 'mesh'
		node.setBundle()		
		node.groupType = 'package'
		filePath = node.getFilePath()
		nodePath = node.getNodePath()

		modelExt = ['.3ds', '.fbx' , '.x', '.lwo', '.obj', '.md5mesh', '.dxf', '.ply', '.stl', '.dae', '.md5anim', '.lws', '.irrmesh', '.nff', '.off', '.blend']
		texExt = ['.bmp', '.jpg','.tif', '.png', '.jpeg' ]

		rootPath = node.getCacheFile( 'meshCache1', is_dir = True, clear =True )
		node.setObjectFile( 'mesh', rootPath )
		# print("mesh importing")
		print(( "root path: " + rootPath ))
		for fileName in os.listdir( node.getAbsFilePath() ):
			fullPath = filePath + '/' + fileName
			name, ext = os.path.splitext( fileName )	

			if ext in modelExt:
				saveFilePath = rootPath + '/mesh'
				print(( "mesh path: " + saveFilePath ))
				# meshPath = node.getCacheFile( 'mesh' )
				# node.setObjectFile( 'mesh',  )
				# print( "fileName: " + fileName )
				# print( "fullPath: " + fullPath)
				# print( "meshPath: " + meshPath )
				# print( "nodePath: " + nodePath )
				scene = pyassimp.load( fullPath )
				pyassimp.export( scene, saveFilePath , "assxml", pyassimp.postprocess.aiProcessPreset_TargetRealtime_MaxQuality )


				# pyassimp.export( scene, "export.xml", "assxml", pyassimp.postprocess.aiProcess_Triangulate )
				# print(mesh.vertices[0])
				pyassimp.release( scene )
				print("mesh imported")


			# elif ext == '.material':
			# 	print( "material" )
			# 	materialPath = node.getCacheFile( 'material' )
			# 	node.setObjectFile( 'material', materialPath )
			# 	print( "materialPath: " + materialPath )
			# 	print( "nodePath: " + nodePath )
				# internalAtlas = _MOCK.convertSpineAtlasToPrebuiltAtlas( fullPath )
				# for page in internalAtlas.pages.values():
				# 	page.source = filePath + '/' + page.texture
				# atlasNode = node.affirmChildNode( node.getBaseName()+'_spine_atlas', 'prebuilt_atlas', manager = 'asset_manager.prebuilt_atlas' )
				# atlasSourceCachePath = atlasNode.getCacheFile( 'atlas_source' )
				# internalAtlas.save( internalAtlas, atlasSourceCachePath )
				# app.getModule( 'texture_library' ).scheduleImport( atlasNode )
			elif ext in texExt:
				saveFilePath = rootPath + '/' + name + '.png'
				print(("texture path: " + saveFilePath ))
				# texturePath = node.getCacheFile( 'texture' )
				# node.setObjectFile( 'texture', texturePath )
				# print( "texturePath: " + texturePath )
				# print( "nodePath: " + nodePath )
				img = Image.open( fullPath )
				img = img.convert( 	"RGBA" )
				img.save( saveFilePath, 'PNG' )


		return True

MeshAssetManager().register()

AssetLibrary.get().setAssetIcon( 'mesh',   'mesh' )
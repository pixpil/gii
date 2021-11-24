import os.path
from gii.core import *
import logging
import shutil
import json

from .ImageHelpers import convertToPNG, convertToWebP, getImageSize
from mock import _MOCK

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class SpineAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.spine'

	def acceptAssetFile(self, filepath):
		if not os.path.isdir(filepath): return False
		if not filepath.endswith( '.spine' ): return False
		return True

	def importAsset(self, node, reload = False ):
		if not node.assetType in [ 'folder', 'spine' ] : return True
		node.assetType = 'spine'
		node.setBundle()		
		filePath = node.getFilePath()
		nodePath = node.getNodePath()
		for fileName in os.listdir( node.getAbsFilePath() ):
			fullPath = filePath + '/' + fileName
			name, ext = os.path.splitext( fileName )
			if ext == '.json':
				skelPath = node.getCacheFile( 'skel' )
				node.setObjectFile( 'skel', skelPath )
				try:
					self._optimizeAnimation( fullPath, skelPath )
				except Exception as e:
					logging.exception( e )
					shutil.copy( fullPath, skelPath )

			elif ext == '.atlas':
				internalAtlas = _MOCK.convertSpineAtlasToPrebuiltAtlas( fullPath )
				for page in list(internalAtlas.pages.values()):
					page.source = filePath + '/' + page.texture
				atlasNode = node.affirmChildNode( node.getBaseName()+'_spine_atlas', 'prebuilt_atlas', manager = 'asset_manager.prebuilt_atlas' )
				atlasSourceCachePath = atlasNode.getCacheFile( 'atlas_source' )
				internalAtlas.save( internalAtlas, atlasSourceCachePath )
				app.getModule( 'texture_library' ).scheduleImport( atlasNode )
				
		return True

	def getPriority(self):
		return 10

	def _optimizeAnimation( self, inputPath, outputPath ):
		def _equalFrame( d1, d2 ):
			n1 = len( d1 )
			n2 = len( d2 )
			if n1!=n2: return False
			for k,v in list(d1.items()):
				if k == 'time' : continue
				if d2.get( k,None ) != v: return False
			return True

		def _optimizeTimeline( srcTimeline ):
			if len( srcTimeline ) < 3 : return srcTimeline
			newTimeline = []
			prevFrame   = None
			dupCount    = 0
			for frame in srcTimeline:
				if prevFrame and _equalFrame( frame, prevFrame ):
					dupCount = dupCount + 1
					if dupCount >= 2: #give up duplicated middle frame( by overwrite )
						newTimeline.pop()
				else:
					dupCount = 0
				newTimeline.append( frame )
				prevFrame = frame
			return newTimeline

		def _loadAndFixJSON( path, **option ):
			fp = file(path)
			raw = fp.read()
			encoding = option.get( 'encoding', 'utf-8' )
			encoded = raw.decode( encoding, 'replace' )
			encoded = encoded.replace('\r\n', '\\r\\n')
			encoded = encoded.replace( '', '?')
			data = json.loads( encoded )
			fp.close()
			return data

		data = _loadAndFixJSON( inputPath )
		animations = data.get( 'animations', None )
		if animations:
			for ani in list(animations.values()):
				boneAnimations = ani.get( 'bones', None )
				if boneAnimations:
					for boneAnimation in list(boneAnimations.values()):
						for key, timeline in list(boneAnimation.items()):
							newtimeline = _optimizeTimeline( timeline )
							boneAnimation[ key ] = newtimeline
						if 'flipX' in boneAnimation:
							del boneAnimation[ 'flipX' ]
						if 'flipY' in boneAnimation:
							del boneAnimation[ 'flipY' ]
				slotAnimations = ani.get( 'slots', None )
				if slotAnimations:
					for slotAnimation in list(slotAnimations.values()):
						for key, timeline in list(slotAnimation.items()):
							newtimeline = _optimizeTimeline( timeline )
							slotAnimation[ key ] = newtimeline
		JSONHelper.trySaveJSON( data, outputPath, indent = 0, sort_keys = False )

	# def deployAsset( self, node, context ):
	# 	super( SpineAssetManager, self ).deployAsset( node, context )
	# 	if not node.isType( 'spine' ): return
	# 	#replace texture		
	# 	# try:
	# 	# 	absAtlasPath = node.getAbsObjectFile('atlas')
	# 	# 	fp = open( absAtlasPath )
	# 	# 	nextLineTexture = False
	# 	# 	textures = []
	# 	# 	for line in fp:
	# 	# 		if nextLineTexture:
	# 	# 			textureName = line.strip()
	# 	# 			textures.append( textureName )
	# 	# 			nextLineTexture = False
	# 	# 		elif line.strip() == '':
	# 	# 			nextLineTexture = True
	# 	# 	fp.close()
	# 	# 	for textureName in textures:
	# 	# 		texturePath = node.getAbsFilePath() + '/' + textureName
	# 	# 		if os.path.exists( texturePath ):
	# 	# 			newPath   = context.addFile( texturePath )
	# 	# 			exportedAtlasPath = context.getAbsFile( node.getObjectFile( 'atlas' ) )
	# 	# 			context.replaceInFile( exportedAtlasPath, textureName, os.path.basename( newPath ) )
	# 	# 			#webp conversion
	# 	# 			fn = context.getAbsFile( texturePath )
	# 	# 			if context.isNewFile( fn ):
	# 	# 				convertToWebP( fn )
	# 	# except Exception, e:
	# 	# 	logging.exception( e )
		

SpineAssetManager().register()

AssetLibrary.get().setAssetIcon( 'spine', 'clip' )

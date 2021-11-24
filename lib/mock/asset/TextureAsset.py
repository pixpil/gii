import os.path
import logging
import subprocess
import shutil
import ujson as json
import sys

from simple_task_queue import task, Task, WorkerPool

from gii.core import *
from mock import _MOCK
from .TextureConverter import convertTextureFormat
from .TextureProcessor import applyTextureProcessor

from . import ImageHelpers 
from PIL import Image

##----------------------------------------------------------------##
signals.register( 'texture.add' )
signals.register( 'texture.remove' )
signals.register( 'texture.rebuild' )

##----------------------------------------------------------------##
_TEXTURE_LIBRARY_DATA_FILE = 'texture_library.json'
_TEXTURE_GROUP_DATA_FILE   = 'texture_groups.json'
_ATLAS_JSON_NAME = 'atlas.json'

@task( 'DeployConvertTexture' )
def taskDeployConvertTexture( srcFormat, dstFormat, src, dst, **option ):
	return convertTextureFormat( srcFormat, dstFormat, src, dst, **option )

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
def groupToJson( group ):
	return {
				'name'               : group.name,
				'filter'             : group.filter,
				'mipmap'             : group.mipmap,
				'wrap'               : group.wrap ,
				'atlas_mode'         : group.atlasMode ,
				'cache'              : group.cache
			}

def _fixPath( path ):
		path = path.replace( '\\', '/' ) #for windows
		if path.startswith('./'): path = path[2:]
		return path	
		

def _changedField( t1, t2 ):
	changed = []
	for key, value in list(t1.items()):
		if t2.get( key, None ) != value:
			changed.append( key )
	return changed

##----------------------------------------------------------------##
def _convertAtlas( inputfile,  srcToAssetDict ):
	f = open( inputfile, 'r' )
	items      = []
	atlasNames = []
	atlasInfos = []
	readingMode = None

	for line in f.readlines():
		if line.startswith( '[atlas]' ):
			readingMode = 'atlas'
			continue

		if line.startswith( '[sprite]' ):
			readingMode = 'sprite'
			continue

		if readingMode == 'atlas':
			parts       = line.split('\t')
			name        = parts[ 0 ]
			atlasNames.append( name )
			atlasInfos.append( {
					'name': os.path.basename(name),
					'size':[ int(parts[1]), int(parts[2]) ]
				} )

		elif readingMode == 'sprite':
			parts       = line.split('\t')
			sourcePath  = _fixPath( parts[1] )
			if sourcePath.startswith('\"'):
				sourcePath = sourcePath[1:-1]		
			# name = os.path.basename( sourcePath )
			assetPath, index, subId = srcToAssetDict[ sourcePath ]
			atlasName = parts[0]		
			atlasId = atlasNames.index( atlasName )
			data = {
				'atlas'  : atlasId,
				'name'   : assetPath,
				'index'  : index,
				'subId'  : subId,
				'source' : sourcePath,
				'rect'   : [ int(x) for x in parts[2:] ]
			}
			items.append(data)

	output = {
		'atlases' : atlasInfos,
		'items'   : items,
	}

	return output

##----------------------------------------------------------------##
class TextureAssetManager( AssetManager ):
	def getName(self):
		return 'asset_manager.texture'

	def getMetaType( self ):
		return 'texture'

	def acceptAssetFile(self, filepath):
		name,ext = os.path.splitext(filepath)
		if os.path.isfile(filepath):
			return ext in [ '.png', '.psd', '.jpg', '.bmp', '.jpeg' ]
		else:
			return ext in ['.texstrip' ]

	def importAsset(self, assetNode, reload = False ):
		logging.info( 'import texture: %s', assetNode.getPath() )
		assetNode.assetType = 'texture'
		texConfig = assetNode.getMetaData( 'texture_config' )
		if not texConfig:
			#add default meta config
			initialConfig = {
				'allowPacked' : True,
				'group' : assetNode.getInheritedMetaData( 'default_texture_group', False ),
				'processor' : None,
				'noGroupProcessor': False,
				'scale' : -1,
			}
			assetNode.setMetaData( 'texture_config', initialConfig )
		if os.path.isdir( assetNode.getAbsFilePath() ):
			assetNode.setBundle()
		TextureLibrary.get().scheduleImport( assetNode ) #let texture library handle real import
		return True

	def deployAsset( self, assetNode, context ):
		super( TextureAssetManager, self ).deployAsset( assetNode, context )
		pixmapPath = assetNode.getObjectFile( 'pixmap' )
		if pixmapPath:
			texLib = app.getModule( 'texture_library' )
			groupNode = texLib.findTextureGroupNode( assetNode )
			if not groupNode: return #WTF?
			if context.checkFileModified( pixmapPath ):
				targetFormat = groupNode.format
				absMappedPath = context.getAbsMappedFile( pixmapPath )
				texLib.convertTextureFormat( absMappedPath, targetFormat, reason = 'deploy' )
				
	def hasAssetThumbnail( self, assetNode ):
		return True

	def buildAssetThumbnail( self, assetNode, targetPath, size ):
		if assetNode.isVirtual():
			srcPath = assetNode.getWorkspaceData( 'source' )
		else:
			srcPath = assetNode.getAbsFilePath()

		if not ImageHelpers.buildThumbnail( srcPath, targetPath, size ):
			return False
		return True

##----------------------------------------------------------------##
class PrebuiltAtlasAssetManager( AssetManager ):
	def getName(self):
		return 'asset_manager.prebuilt_atlas'

	def importAsset(self, node, reload = False ):
		TextureLibrary.get().scheduleImport( node ) #let texture library handle real import
		return True

	def deployAsset( self, assetNode, context ):
		super( PrebuiltAtlasAssetManager, self ).deployAsset( assetNode, context )
		texLib = app.getModule( 'texture_library' )
		groupNode = texLib.findTextureGroupNode( assetNode )
		if not groupNode: return #WTF?
		targetFormat = groupNode.format
		for key, value in list(assetNode.objectFiles.items()):
			if not key.startswith( 'pixmap' ): continue
			pixmapPath = value
			if context.checkFileModified( pixmapPath ):
				absMappedPath = context.getAbsMappedFile( pixmapPath )
				texLib.convertTextureFormat( absMappedPath, targetFormat, reason = 'deploy' )

##----------------------------------------------------------------##
class TextureLibrary( EditorModule ):
	_singleton = None
	@staticmethod
	def get():
		return TextureLibrary._singleton

	def __init__( self ):
		assert not TextureLibrary._singleton
		TextureLibrary._singleton = self
		self.lib = None
		self.pendingImportTextures = {}
		self.pendingUpdateGroups = {}
		self.pendingUpdate = False

	def getName( self ):
		return 'texture_library'

	def getDependency( self ):
		return ['mock']

	def needUpdate( self ):
		return True

	def onLoad( self ):
		self.lib = _MOCK.getTextureLibrary()

		self.dataPath      = self.getProject().getConfigPath( _TEXTURE_LIBRARY_DATA_FILE )		
		self.groupDataPath = self.getProject().getConfigPath( _TEXTURE_GROUP_DATA_FILE )

		self.delegate  = app.getModule('moai').loadLuaDelegate( _getModulePath('TextureLibraryHelper.lua') )

		signals.connect( 'app.ready', self.postAppReady )

		signals.connect( 'asset.post_import_all', self.postAssetImportAll )
		signals.connect( 'asset.unregister',      self.onAssetUnregister )

		signals.connect( 'project.deploy', self.onDeploy )
		signals.connect( 'project.presave', self.preSaveProject )
		signals.connect( 'app.pre_start', self.preAppStart )

	def onStart( self ):
		# self.updateConfigData()
		pass

	def preAppStart( self ):
		self.updateConfigData()

	def postAppReady( self ):
		if not os.path.exists( self.dataPath ):
			self.saveIndex()
		for group in list(self.lib.groups.values()):
			if group.atlasCachePath:
				CacheManager.get().touchCacheFile( group.atlasCachePath )

	def getLibrary( self ):
		return self.lib

	def onUpdate( self ):
		if self.pendingUpdate:
			self.doPendingImports()

	def saveIndex( self ):
		logging.info( 'saving texture library index' )
		self.lib.save( self.lib, self.dataPath )
		self.saveConfigData()

	def saveConfigData( self ):
		#save group data to config folder
		self.lib.saveGroupDataToFile( self.lib, self.groupDataPath )
		#save texture item settings in each's own meta data
		configDataDict = self.lib.collectTextureConfigData( self.lib )
		assetLib = self.getAssetLibrary()
		for path, data in list(configDataDict.items()):
			node = assetLib.getAssetNode( path )
			if node:
				output = {
					'group'              : data[ 'group' ],
					'scale'              : data[ 'scale' ],
					'processor'          : data[ 'processor' ],
					'noGroupProcessor'   : data[ 'noGroupProcessor' ],
					'allowPacked'        : data[ 'allowPacked' ],
				}
				node.setMetaData( 'texture_config', output )
			else:
				logging.warn( 'cannot find asset node:' + path )

	def updateConfigData( self ):
		#cached library data is loaded in mock runtime.
		lib = self.lib
		lib.updateGroupDataFromFile( lib, self.groupDataPath )
		#we need to check if any of the meta_data/group_datas is changed 
		assetLib = self.getAssetLibrary()
		for asset in assetLib.enumerateAsset( 'texture' ):
			self.updateTextureConfigData( asset )

	def updateTextureConfigData( self, assetNode ):
		texConfig = assetNode.getMetaData( 'texture_config', None )
		if not texConfig:
			#add default meta config
			texConfig = {
				'allowPacked' : True,
				'group' : assetNode.getInheritedMetaData( 'default_texture_group', False ),
				'processor' : None,
				'noGroupProcessor' : False,
				'scale' : -1,
			}
			assetNode.setMetaData( 'texture_config', texConfig )
		if texConfig.get( 'noGroupProcessor', None ) == None:
			texConfig[ 'noGroupProcessor' ] = False
			
		path = assetNode.getPath()
		lib = self.lib
		lib.updateTextureConfig( lib, path, texConfig )

	def findTextureNode( self, assetNode ):
		lib = self.lib
		t = lib.findTexture( lib, assetNode.getNodePath() )
		return t

	def findTextureGroupNode( self, assetNode ):
		texNode = self.findTextureNode( assetNode )
		if not texNode: return None
		return texNode.parent

	def scheduleUpdate( self ):
		self.pendingUpdate = True

	def scheduleImport( self, assetNode, modifyState = None ):
		lib = self.lib
		t = lib.findTexture( lib, assetNode.getNodePath() )
		if not t:
			t = lib.addTexture( lib, assetNode.getNodePath() )
			assert t
			signals.emit( 'texture.add', t )
		else:
			t.modifyState = 'all'
		self.updateTextureConfigData( assetNode )
		self.scheduleUpdate()

	def scheduleUpdateGroup( self, groupNode, modifyState = None ):
		if modifyState:
			groupNode.setModifyState( groupNode, modifyState )
		self.scheduleUpdate()

	def scheduleUpdateTexture( self, texNode, modifyState = None ):
		if modifyState:
			texNode.setModifyState( texNode, modifyState )
		self.scheduleUpdate()
		
	def doPendingImports( self ):
		lib = self.getLibrary()
		assetLib = self.getAssetLibrary()
		#collect all modifystates
		lib.updateModifyState( lib )
		modifiedGroups = set()
		modifiedTextures = set()
		#get modified
		for group, modifyState in list(lib.modifiedGroups.items()):
			logging.info( 'group modifystate update: %s, %s ', group.name, modifyState )
			modifiedGroups.add( group )
			# if modifyState in [ 'file', 'atlas' ]:
			# 	for i, tex in group.textures.items():
			# 		modifiedTextures.add( tex )

		for tex, modifyState in list(lib.modifiedTextures.items()):
			logging.info( 'texture update: %s, %s' % ( tex.path, modifyState ) )
			modifiedTextures.add( tex )

		#update texture nodes
		for tex in modifiedTextures:
			group = tex.parent
			assetNode = assetLib.getAssetNode( tex.path )
			if not assetNode:
				logging.warn( 'cannot find asset node:' + tex.path )
				continue
			self.processTextureNode( tex, assetNode )
			if group.isAtlas( group ):
				group.setModifyState( group, 'atlas' )
				modifiedGroups.add( group )
			else:
				self.buildSingleTexture( tex, assetNode )

		#update groups
		for group in modifiedGroups:
			modifyState = group.modifyState
			if modifyState in [ 'file', 'atlas' ]:
				if group.isAtlas( group ):
					self.buildAtlas( group )	

		#done
		lib = self.getLibrary()
		lib.clearModifyState( lib )
		self.pendingUpdate = False
		self.saveIndex()

	##----------------------------------------------------------------##
	def processTextureNode( self, tex, assetNode ):
		logging.info( 'processing texture: %s' % assetNode.getNodePath() )

		if assetNode.isType( 'texture' ):
			assetNode.clearCacheFiles()
			if assetNode.isVirtual():
				src = assetNode.getWorkspaceData( 'source', assetNode.getMetaData( 'source', None ) )
				if not src:
					raise Exception( 'virtual texture node has no source metadata given' )
				src = AssetLibrary.get().getAbsProjectPath( src )
			else:
				src = assetNode.getAbsFilePath()
			dst = assetNode.getAbsCacheFile( 'pixmap' ) 
			#resize first
			self._processTexture( src, dst, tex )

		elif assetNode.isType( 'prebuilt_atlas' ):
			atlasSourcePath = assetNode.getCacheFile( 'atlas_source' )
			atlas = self.delegate.call( 'loadPrebuiltAtlas', atlasSourcePath )
			pageId = 0
			for page in list(atlas.pages.values()):
				pageId += 1
				src = self.getAssetLibrary().getAbsProjectPath( page.source )
				dst = assetNode.getCacheFile( 'pixmap_%d' % pageId )
				assetNode.setObjectFile( 'pixmap_%d' % pageId, dst )
				self._processTexture( src, dst, tex )
				if page.w < 0:
					w, h = ImageHelpers.getImageSize( dst )
					page.w = w
					page.h = h
			assetNode.setMetaData( 'page_count', pageId )			
			atlasOutputPath = assetNode.getCacheFile( 'atlas' )
			assetNode.setObjectFile( 'atlas', atlasOutputPath )
			tex.prebuiltAtlasPath = atlasOutputPath
			atlas.save( atlas, atlasOutputPath )

		else:
			raise Exception( 'unknown texture node type!!' )

	def _processTexture( self, src, dst, tex ):
		#convert single image
		group = tex.parent
		try:
			options = {
				'premultiply_alpha' : False
			}
			if group:
				options[ 'premultiply_alpha' ] = group.premultiplyAlpha

			result = ImageHelpers.convertToPNG( src, dst, **options )
			scale = tex.getScale( tex )
			if scale != 1 :
				img = Image.open( dst )
				ow, oh = img.size
				w   = int( max( ow*scale, 1 ) )
				h   = int( max( oh*scale, 1 ) )
				img = img.resize( (w,h), Image.BILINEAR )
				img.save( dst, 'PNG' )
		except Exception as e:
			#fallback image
			img = Image.new( "RGBA", ( 32, 32 ), color=(0, 255, 0, 255) )
			img.save( dst, 'PNG' )
			return False

		#apply processor on dst file
		if group:
			groupProcessor = group.processor
			if groupProcessor and ( not tex.noGroupProcessor ):
				applyTextureProcessor( groupProcessor, dst )

			nodeProcessor = tex.processor
			if nodeProcessor:
				applyTextureProcessor( nodeProcessor, dst )				

	def convertTextureFormat( self, src, dstFormat, dst = None, **option ):
		if option.get( 'reason', None ) == 'deploy':
			Task( 'DeployConvertTexture' ).promise( None, dstFormat, src, dst, **option )
		else:
			return convertTextureFormat( None, dstFormat, src, dst, **option )

	##----------------------------------------------------------------##
	def _explodePrebuiltAtlas( self, node, srcToAssetDict, sourceList, outputDir, prefix, scale ):
		atlasSourcePath = node.getCacheFile( 'atlas_source' )
		atlas = self.delegate.call( 'loadPrebuiltAtlas', atlasSourcePath )
		nodePath = node.getNodePath()
		pageId = 0		
		for page in list(atlas.pages.values()):
			pageId += 1
			imagePath = node.getCacheFile( 'pixmap_%d' % pageId )
			img = Image.open( imagePath )
			itemId = 0
			for item in list(page.getItems( page ).values()):
				itemId += 1
				if item.rotated:
					box  = ( item.x, item.y, item.x + item.h, item.y + item.w )
				else:
					box  = ( item.x, item.y, item.x + item.w, item.y + item.h )
				part = img.crop( box )
				partName = '%s_%d_%d.png' % ( prefix, pageId, itemId )
				partPath = outputDir( partName )
				if scale != 1:
					w, h = part.size
					newSize = ( max( 1, int(w*scale) ),  max( 1, int(h*scale) ) )
					part = part.resize( newSize, Image.BILINEAR )
				part.save( partPath )
				srcToAssetDict[ partPath ] = ( nodePath, pageId , item.name )
				sourceList.append( partPath )

	def buildAtlas( self, group ):
		texItems = list( group.textures.values() )
		if not texItems: 
			logging.info( 'empty group:' + group.name )
			return True
		
		logging.info( '' )
		logging.info( 'building atlas texture:' + group.name )

		#packing atlas
		assetLib = self.getAssetLibrary()
		nodes = {}

		for t in texItems:
			node = assetLib.getAssetNode( t.path )
			if node:
				nodes[ node ] = t				
			else:
				logging.warn( 'node not found: %s' % t.path )

		sourceList     = []
		srcToAssetDict = {}
		prebuiltAtlases = []

		for node in nodes:
			if node.isType( 'texture' ):
				path = node.getAbsCacheFile( 'pixmap' )
				tex = nodes[ node ]
				# scale = tex.getScale( tex )
				# if scale != 1 :
				# 	img = Image.open( path )
				# 	ow, oh = img.size
				# 	w   = int( max( ow*scale, 1 ) )
				# 	h   = int( max( oh*scale, 1 ) )
				# 	img = img.resize( (w,h), Image.BILINEAR )
				# 	img.save( path, 'PNG' )
				sourceList.append( path )
				srcToAssetDict[ path ] = ( node.getNodePath(), 0, False )

			elif node.isType( 'prebuilt_atlas' ):
				prebuiltAtlases.append( node )

		explodedAtlasDir = None
		if group.repackPrebuiltAtlas:
			explodedAtlasDir = CacheManager.get().getTempDir()		
			atlasId = 0
			for node in prebuiltAtlases:
				atlasId += 1
				texture = group.findTexture( group, node.getNodePath() )				
				scale  = texture.getScale( texture )
				prefix = 'atlas%d' % atlasId
				self._explodePrebuiltAtlas(
					node, srcToAssetDict, sourceList, explodedAtlasDir, prefix, scale
				)
		else:
			for node in prebuiltAtlases:
				nodePath = node.getNodePath()
				pageCount = node.getMetaData( 'page_count' )
				for i in range( pageCount ):
					path = node.getAbsCacheFile( 'pixmap_%d' % ( i + 1 ) )
					srcToAssetDict[ path ] = ( nodePath, i + 1, False )
					sourceList.append( path )

		#use external packer
		atlasName = 'atlas_' + group.name

		tmpDir = CacheManager.get().getTempDir()
		prefix = tmpDir( atlasName )

		outputDir = CacheManager.get().getCacheDir( '<texture_group>/' + group.name  )
		for name in os.listdir( outputDir ): #clear target path
			try:
				os.remove( outputDir + '/' + name )
			except Exception as e:
				pass
		arglist = [ sys.executable, _getModulePath('tools/AtlasGenerator.py'), '--prefix', prefix ]
		arglist += [ str( group.maxAtlasWidth ) , str( group.maxAtlasHeight ) ]
		arglist += sourceList
		
		if sourceList:
			try:
				ex = subprocess.call( arglist ) #run packer
				#conversion
				srcFile = prefix + '.txt'
				data    = _convertAtlas( srcFile,  srcToAssetDict )
				dstPath = outputDir
				#copy generated atlas
				for i, entry in enumerate( data['atlases'] ):
					src = entry['name']
					dstName = 'tex_%d' % i
					# dst = '%s/%s%d' % ( dstPath, atlasName, i )
					entry['name'] = dstName
					dstFile = dstPath +'/' + dstName
					shutil.copy( tmpDir( src ), dstFile )
				#update texpack
				data[ 'sources' ] = sourceList
				
				cfgPath = outputDir + '/' + _ATLAS_JSON_NAME
				with open( cfgPath, 'w' ) as fp:
					json.dump( data, fp, sort_keys=True, indent=2 )

			except Exception as e:
				logging.exception( e )
				return False

			self.delegate.call( 'fillAtlasTextureGroup', group, outputDir, group.repackPrebuiltAtlas )
			self.delegate.call( 'releaseTexPack', outputDir )

			#redirect asset node to sub_textures
			group.unloadAtlas( group )
			for node in nodes:
				self.buildSubTexture( group, node )

			return True

		else:
			return True


	def buildSingleTexture( self, tex, node ):
		group = tex.parent
		logging.info( 'building single texture: %s<%s>' % ( node.getPath(), group.name ) )
		if node.isType( 'texture' ):
			node.clearObjectFiles()
			dst = node.getCacheFile( 'pixmap' )
			node.setObjectFile( 'pixmap', dst )
			img = Image.open( dst )
			ow, oh = img.size
			w, h = img.size
			scale = tex.getScale( tex )
			if scale != 1:
				newSize = ( int(w*scale), int(h*scale) )
				img = img.resize( newSize, Image.BILINEAR )
				img.save( dst, 'PNG' )
				w, h = newSize
			self.delegate.call( 'fillSingleTexture', tex, dst, w, h, ow, oh )

		elif node.isType( 'prebuilt_atlas' ):
			count = node.getMetaData( 'page_count' )
			scale = tex.getScale( tex )
			if scale != 1:
				atlasOutputPath = node.getCacheFile( 'atlas' )
				atlas = self.delegate.call( 'loadPrebuiltAtlas', atlasOutputPath )
				atlas.rescale( atlas, scale )
				for i in range( count ):
					dst = node.getCacheFile( 'pixmap_%d' % ( i + 1 ) )
					img  = Image.open( dst )
					w, h = img.size
					w1   = max( int(w*scale), 1 )
					h1   = max( int(h*scale), 1 )
					img  = img.resize( ( w1, h1 ), Image.BILINEAR )
					img.save( dst, 'PNG' )
				atlas.save( atlas, atlasOutputPath )

		signals.emit( 'texture.rebuild', node )

	def buildSubTexture( self, group, node ):
		logging.info( 'building sub texture: %s<%s>' % ( node.getPath(), group.name ) )
		if node.isType( 'texture' ):
			node.clearObjectFiles()
			node.setObjectFile( 'pixmap', None ) #remove single texture if any
			# node.setObjectFile( 'config', node.getCacheFile( 'config' ) )
			# JSONHelper.trySaveJSON( groupToJson( group ), node.getAbsObjectFile( 'config' ) )
		elif node.isType( 'prebuilt_atlas' ):
			pass
		signals.emit( 'texture.rebuild', node )	
		
	def postAssetImportAll( self ):
		self.doPendingImports()

	def onAssetUnregister( self, node ):
		t = self.lib.removeTexture( self.lib, node.getNodePath() )
		if t:
			logging.info( 'texture removed from library %s', node.getPath() )
			signals.emit( 'texture.remove', t )
		else:
			if node.getType() == 'texture':
				logging.warning( 'texture to be removed not found in library %s', node.getPath() )
		self.scheduleUpdate()

	def forceRebuildAllTextures( self ):
		for assetNode in self.getAssetLibrary().enumerateAsset( 'texture' ):
			self.scheduleImport( assetNode )
		self.doPendingImports()

	def forceRebuildTexture( assetNode ):
		self.scheduleImport( assetNode )
		self.doPendingImports()

	def onDeploy( self, context ):
		self.saveIndex()
		packedIndexPath = context.addConfigFile( self.dataPath, name = 'texture_index' )
		absPackedIndexPath = context.getAbsMappedFile( self.dataPath )
		context.setMeta( 'mock_texture_library', packedIndexPath )
		#process atlas
		for group in list(self.lib.groups.values()):
			if group.isAtlas( group ) and group.atlasCachePath:
				srcPath = group.atlasCachePath
				packedPath = context.addFileToPackage( srcPath, 'asset' )
				absPackedPath = context.getPath( packedPath )
				if not os.path.isdir( absPackedPath ):
					logging.warning( 'asset path not found:' + repr(self) )
					continue
					
				for f in os.listdir( absPackedPath ):
					if not f.startswith( 'tex' ): continue
					fullPath = absPackedPath + '/' + f
					if context.isNewerFile( fullPath ):
						self.convertTextureFormat( fullPath, group.format, reason = 'deploy' )
				#replace in index file
				context.replaceInFile( absPackedIndexPath, srcPath, packedPath )
		
	def preSaveProject( self, prj ):
		self.saveIndex()

##----------------------------------------------------------------##
TextureAssetManager().register()
PrebuiltAtlasAssetManager().register()

TextureLibrary().register()

AssetLibrary.get().setAssetIcon( 'prebuilt_atlas', 'cell' )

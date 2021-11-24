import os.path
import json
import base64
import hashlib
from gii.core import *
from mock import _MOCK, _MOCK_EDIT, isMockInstance, getMockClassName
from util.FileTool import calcFileMD5

##----------------------------------------------------------------##
SCENE_INDEX_NAME   = 'scene_index.json'
SCENE_GROUP_EXTENSION = '.scene_group'
PACKED_SCENE_GROUP_EXTENSION = '.packed'

##----------------------------------------------------------------##
class SceneAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.scene'

	def acceptAssetFile( self, filePath ):
		name,ext = os.path.splitext(filePath)
		if not ext in ['.scene']: return False
		if os.path.isdir( filePath ):
			indexData = JSONHelper.tryLoadJSON( filePath + '/' + SCENE_INDEX_NAME )
			return indexData and indexData.get( '_assetType', None ) == 'scene'
		elif os.path.isfile(filePath):
			#legcacy support
			data = JSONHelper.tryLoadJSON( filePath )
			return data and data.get( '_assetType', None ) == 'scene'	
		else:
			return False

	def importAsset( self, node, reload = False ):
		if node.isVirtual(): return
		if os.path.isdir( node.getFilePath() ):
			return self.importScene( node, reload )
		elif os.path.isfile( node.getFilePath() ):
			return self.importLegacyScene( node, reload )

	def extractProtoData( self, data, node, filePath ):
		protoInfos = data.get( 'protos', None )
		if protoInfos:
			for protoInfo in protoInfos:
				name       = protoInfo[ 'name' ]
				serialized = protoInfo[ 'serialized' ]
				protoNode = node.affirmChildNode( name, 'proto', manager = self )
				protoDataFile = protoNode.getAbsCacheFile( 'data' )
				if os.path.isfile( protoDataFile ):
					hashValue0 = calcFileMD5( protoDataFile )
				else:
					hashValue0 = None
				decoded = base64.b64decode( serialized ) 
				hashValue1 = hashlib.md5( decoded ).hexdigest()
				if hashValue0 and hashValue0 == hashValue1:
					protoNode.modifyState = 'ignored'
				protoNode.setObjectFile( 'def', protoNode.getCacheFile( 'data' ) )
				protoNode.setObjectFile( 'packed_def', protoNode.getCacheFile( 'packed_def' ) )
				with open( protoNode.getAbsCacheFile( 'data' ), 'wb' ) as fp:
					fp.write( decoded )

				JSONHelper.convertJSONFileToMsgPack( protoNode.getAbsCacheFile( 'data' ), protoNode.getAbsCacheFile( 'packed_def' ) )
				#extract data and
		return True

	def importScene( self, node, reload = False ):
		#TODO: duplicated proto name detection
		node.setBundle()
		node.assetType = 'scene'
		node.groupType = 'package'
		
		compiledPath = node.getCacheDir( 'compiled' )
		node.setObjectFile( 'compiled', compiledPath )
		node.setObjectFile( 'def', node.getFilePath() )

		basePath = node.getFilePath()
		
		indexData = JSONHelper.tryLoadJSON( basePath + '/' + SCENE_INDEX_NAME )
		if not indexData:
			logging.warn( 'invalid scene index file: %s' % node.getPath() )
			return False
		
		packedIndexPath = compiledPath + '/' + SCENE_INDEX_NAME + '.packed'
		JSONHelper.saveMsgPack( indexData, packedIndexPath )

		for fileName in os.listdir( basePath ):
			name, ext = os.path.splitext( fileName )
			filePath = basePath + '/' + fileName
			if ext == SCENE_GROUP_EXTENSION:
				data = JSONHelper.tryLoadJSON( filePath )
				if not data:
					logging.warn( 'invalid scene group file: %s' % filePath )
					continue
				self.extractProtoData( data, node, filePath )
				packedPath = compiledPath + '/' + fileName + '.packed'
				JSONHelper.saveMsgPack( data, packedPath )

		return True

	def importLegacyScene( self, node, reload = False ):
		node.assetType = 'scene'
		node.groupType = 'package'

		filePath = node.getFilePath()
		node.setObjectFile( 'def', filePath )
		#scan proto nodes
		data = JSONHelper.tryLoadJSON( filePath )
		if not data: return True
		self.extractProtoData( data, node, filePath )
		return True

	def editAsset( self, node ):
		editor = app.getModule( 'scenegraph_editor' )
		if not editor:
			return alertMessage( 'Editor not load', 'Scene Editor not found!' ) 
		if node.assetType == 'scene':
			editor.openScene( node )
		elif node.assetType == 'proto':
			scnNode = node.getParent()
			if editor.activeSceneNode == scnNode:
				editor.locateProto( node )
			else:
				callLocating = signals.callOnce( 'scene.change', lambda: editor.locateProto( node ) )
				if not editor.openScene( scnNode ):
					signals.dropCall( callLocating )
		else:
			return

	def hasAssetThumbnail( self, assetNode ):
		if assetNode.getType() == 'proto': return True
		return False

	def buildAssetThumbnail( self, assetNode, targetPath, size ):
		nodePath = assetNode.getPath()
		w, h = size
		if _MOCK_EDIT.buildProtoThumbnail( nodePath, targetPath, w, h ):
			return True
		else:
			return False


##----------------------------------------------------------------##
class SceneCreator(AssetCreator):
	def getAssetType( self ):
		return 'scene'

	def getLabel( self ):
		return 'Scene'

	def createLegacyScene( self, fullPath ):
		fp = open( fullPath, 'w' )
		data={
			'_assetType' : 'scene', #checksum
			'map'     :{},
			'entities':[]
		}
		json.dump( data, fp, sort_keys=True, indent=2 )
		fp.close()
		return True

	def createEmptyScene( self, fullPath ):
		os.mkdir( fullPath )
		emptyIndexData = {
			'_assetType' : 'scene', #checksum
			'config' : {},
			'scenes' : []
		}
		JSONHelper.trySaveJSON( emptyIndexData, fullPath + '/' + SCENE_INDEX_NAME )
		return True

	def createAsset( self, name, contextNode, assetType ):		
		ext = '.scene'
		filename = name + ext
		if contextNode.isType('folder'):
			nodePath = contextNode.getChildPath( filename )
		else:
			nodePath = contextNode.getSiblingPath( filename )
		fullPath = AssetLibrary.get().getAbsPath( nodePath )
		if os.path.exists(fullPath):
			raise Exception( 'File already exist:%s' % fullPath )
		# self.createLegacyScene( fullPath )
		self.createEmptyScene( fullPath )
		return nodePath

##----------------------------------------------------------------##
SceneAssetManager().register()
SceneCreator().register()

AssetLibrary.get().setAssetIcon( 'scene',    'scene' )
AssetLibrary.get().setAssetIcon( 'proto',    'proto' )

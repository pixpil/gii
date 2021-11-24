# import json
import ujson as json
import msgpack
import re
import os
import logging
import os.path
import weakref
import shutil
import time

from abc import ABCMeta, abstractmethod

from . import JSONHelper
from . import signals
from . import AssetUtils
from .helpers import makeMangledFilePath

from .cache import CacheManager

from .mime import GII_MIME_ASSET_LIST

from util import TagMatch
from util import RemoteFile

import hashlib

GII_ASSET_INDEX_PATH        = 'asset_table.json'
GII_ASSET_INDEX_OUTPUT_PATH = 'asset_table.output'
GII_REMOTE_FILE_INDEX_PATH = 'remote_table.json'
GII_ASSET_META_DIR         = '.assetmeta'
GII_ASSET_WORKSPACE_DIR    = 'asset'

GII_REMOTE_DIR             = '.remote'

metaPattern = re.compile( '^(.*/)\.assetmeta/(.*)\.meta$')

##----------------------------------------------------------------##
def deepEq( v0, v1 ):
	t0 = type( v0 )
	t1 = type( v1 )
	if t0 == t1:
		if t0 == dict:
			if len( v0 ) != len( v1 ): return False
			for k, a in v0.items():
				b = v1.get( k, None )
				if not deepEq( a, b ): return False
			return True

		elif t0 == list:
			if len( v0 ) != len( v1 ): return False
			for i, a  in enumerate( v0 ):
				b = v1[ i ]
				if not deepEq( a, b ): return False
			return True
			
	return v0 == v1


##----------------------------------------------------------------##
def _affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False

##----------------------------------------------------------------##
class AssetException(Exception):
	pass

##----------------------------------------------------------------##
class AssetNode(object):
	def __init__(self, nodePath, assetType='file', **kwargs):	
		self.nodePath   = nodePath
		self.assetType  = assetType
		self.groupType  = assetType == 'folder' and 'folder' or None
		self.parentNode = None

		self.metadata   = None
		self.workspaceState = None
		self.tags       = []
		self.tagCache   = None
		self.inheritedTags = None

		self.readonly  = False

		self.name = os.path.basename( nodePath )
		self.shortName = self.name
		
		self.children = []
		self.dependency     = {}     #runtime level dependency
		self.depBy   = {}     #runtime level dependency

		self.deployStorageMode = False #for storage

		self.cacheFiles  = {}
		self.objectFiles = {}

		self.deployState = None
		self.modifyState = 'new'		
		self.metaDataDirty = False

		self.filePath = kwargs.get( 'filePath', nodePath )
		self.fileTime = kwargs.get( 'fileTime', 0 )
		self.metaTime = kwargs.get( 'metaTime', 0 )
		self.fileType = None

		self.managerVersion = 0
		self.currentMetaHash = None

		manager = kwargs.get( 'manager', None )
		if isinstance( manager, AssetManager ):
			self.managerName = manager.getName()
		else:
			self.managerName = manager

		self.properties={}		

	def __repr__(self):	
		return '<{0}>{1}'.format( self.getType(), self.getNodePath() )

	def getType(self):
		return self.assetType

	def getMetaType( self ):
		mgr = self.getManager()
		if mgr: return mgr.getMetaType()
		return None

	def getGroupType( self ):
		return self.groupType

	def isType(self, *typeNames ):
		return self.assetType in list( typeNames )

	def isGroupType(self, *typeNames ):
		return self.groupType in list( typeNames )

	def isFolder( self ):
		return self.isType( 'folder' )

	def getRemoteFileNode( self ):
		 return AssetLibrary.get().getRemoteFileNode( self.nodePath )

	def getRemoteSourceFiles( self ):
		remoteNode = self.getRemoteFileNode() 
		if not remoteNode: return []
		return remoteNode.getSourceFileList()

	def isRemoteFile( self ):
		if self.getRemoteFileNode():
			return True
		else:
			return False

	def isParentRemoteFile( self ):
		p = self.parentNode
		while p:
			if p.isRemoteFile():
				return True
			p = p.parentNode
		return False

	def getManager(self, fallbackToRaw = True ):
		return AssetLibrary.get().getAssetManager( self.managerName, fallbackToRaw )

	def checkManagerVersion(self):
		if not self.managerName: return True #ignore raw

		manager = self.getManager( False )
		if not manager: #manager missing, need reimport
			return False

		return manager.getVersion() == self.managerVersion

	def buildSearchInfo( self, **options ):
		manager = self.getManager()
		if manager:
			return manager.buildAssetSearchInfo( self, **options )
		return None 

	def requestThumbnail( self, size, force = False ):
		manager = self.getManager()
		if manager:
			return manager.requestAssetThumbnail( self, size, force )
		return None

	def clearThumbnails( self ):
		thumbnails = []
		for id in self.cacheFiles:
			if id.startswith( 'thumbnail@' ):
				thumbnails.append( id )
		for id in thumbnails:
			del self.cacheFiles[ id ]

	def getThumbnailPath( self, size, affirm = False ):
		thumbId = 'thumbnail@'+repr(size)
		return self.getAbsCacheFile(
			thumbId, 
			category = 'thumbnail',
			affirm   = affirm
		)

	def getName(self):
		return self.name

	def getBaseName(self):
		name, ext = os.path.splitext(self.name)
		return name

	def getShortName( self ):
		return self.shortName

	def getPathDepth(self):
		return self.nodePath.count('/')

	def getPath(self):
		return self.nodePath	

	def getMangledName( self ):
		return makeMangledFilePath( self.getPath() )

	def getNodePath( self ):
		return self.nodePath

	def getDir(self):
		return os.path.dirname( self.getNodePath() )

	def getFileDir( self ):
		return os.path.dirname( self.getFilePath() )

	def isRegistered( self ):
		return AssetLibrary.get().hasAssetNode( self.nodePath )

	def getSiblingPath(self,name):
		if self.getDir():
			return self.getDir() + '/' + name
		else:
			return name

	def getSiblingFilePath( self, name ):
		if self.getFileDir():
			return self.getFileDir() + '/' + name
		else:
			return name

	def getChildPath(self, name):
		path = self.getPath()
		if path:
			return path + '/' + name
		else:
			return name

	def getNodePath(self):
		return self.nodePath

	def isVirtual(self):
		if self.filePath: return False
		return True

	def getSibling(self, name):
		return self.parentNode.getChild(name)

	def getChild(self, name):
		for n in self.children:
			if n.getName() == name:
				return n
		return None

	def hasChild(self):
		return len(self.children)>0

	def getParent(self):
		return self.parentNode

	def addChild(self, node):
		self.children.append(node)
		node.parentNode = self
		return node

	def isChildOf( self, node ):
		p = self.parentNode
		while p:
			if p == node: return True
			p = p.parentNode
		return False

	def isParentOf( self, node ):
		return node.isChildOf( self )

	def affirmChildNode( self, name, assetType, **kwargs ):
		node = self.getChild( name )
		if not node:
			return self.createChildNode( name, assetType, **kwargs )
		else:
			node.assetType = assetType
			manager = kwargs.get( 'manager', None )
			if isinstance( manager, str ):
				node.managerName = manager
			elif isinstance( manager, AssetManager ):
				node.managerName = manager.getName()
		node.modifyState = False
		return node

	def createChildNode(self, name, assetType, **kwargs):
		path = self.nodePath + '/' + name
		if 'filePath' not in kwargs: kwargs['filePath'] = False
		node = AssetNode(path, assetType, **kwargs)
		self.addChild( node )

		if self.isRegistered():
			AssetLibrary.get().registerAssetNode( node )
		else:
			#will be registered along with parent node
			pass
		return node

	def setBundle( self, isBundle = True ):
		self.setProperty( 'is_bundle', isBundle )
		if isBundle:
			pass

	def isBundle( self ):
		return self.getProperty( 'is_bundle', False )

	def setManager(self, assetManager, forceReimport=False):
		prevManager = self.getManager()
		if prevManager != assetManager:
			prevManager.dropAsset( self )
			self.managerName = assetManager.getName()
		#TODO: validation? reimport?

	def removeChild(self, node):
		idx=self.children.index(node)
		self.children.pop(idx)
		node.parentNode=None

	def addDependency( self, key, depNode ):
		if isinstance( depNode, str ):
			depNode = AssetLibrary.get().getAssetNode( depNode )
		if not depNode:
			return
		self.dependency[ key ] = depNode.getNodePath()
		depNode.depBy[ self.getNodePath() ] = True

	def removeDependency( self, key ):
		depPath = self.dependency.get( key, None )
		if not depPath: return
		lib  = AssetLibrary.get()
		dep = lib.getAssetNode( depPath )
		if dep:
			del dep.depBy[ self.getNodePath() ]
		del self.dependency[ key ]

	def clearDependency( self ):
		lib  = AssetLibrary.get()
		path = self.getNodePath()
		for key, depPath in self.dependency.items():
			dep = lib.getAssetNode( depPath )
			if dep:
				del dep.depBy[ path ]
		self.dependency.clear()

	def getDependency( self, key ):
		return self.dependency.get( key, None )
		
	def getDependencyNode( self, key ):
		path = self.dependency.get( key, None )
		return path and AssetLibrary.get().getAssetNode( path )

	def findDependencyKey( self, node ):
		path = node.getNodePath()
		for k, v in self.dependency.items():
			if v==path: return k
		return None

	def getDeployState(self):
		if self.deployState == False:
			return False
		if self.deployState == True:
			return True
		if not self.parentNode: return None		#root
		pstate = self.parentNode.getDeployState()
		if pstate == False: return False
		if pstate: return 'parent'
		lib = AssetLibrary.get()
		for nodePath in self.depBy:
			node = lib.getAssetNode( nodePath )
			if node and node.getDeployState():
				return 'dependency'
		return None

	def setDeployState(self, state):
		if self.deployState == state: return
		self.deployState = state
		signals.emit('asset.deploy.changed', self)

	def getDeployConfig(self):
		manager = self.getManager()
		if not manager:
			return {
				'policy' :False,
				'package':False
			}
		else:
			return manager.getAssetDeployConfig( self )

	def markModified( self, forceMarkChildren = False ):
		self.markSelfModified()
		if forceMarkChildren:
			self.markChildrenModified()

	def markSelfModified( self ):
		if self.modifyState == 'new': return
		logging.info( 'mark modified: %s', repr(self) )
		manager = self.getManager()
		self.clearThumbnails()
		if manager:
			manager.markModified( self )
		else:
			self.modifyState = 'modified'

	def markChildrenModified( self ):
		for child in self.children:
			child.markSelfModified()
			child.markChildrenModified()

	def isReady( self ): #TODO
		if self.modifyState: return False
		return self.ready

	def touch( self ):
		fname = self.getAbsFilePath()
		if fname:
			if os.path.isfile( fname ):
				with open(fname, 'a'):
					os.utime(fname, None)

	def getFilePath(self):
		return self.filePath

	def getFileType( self ):
		return self.fileType

	def detectFileType( self ):
		if not self.filePath: return 'v'
		path = self.getAbsFilePath()
		if os.path.isdir( path ):
			return 'd'
		elif os.path.isfile( path ):
			return 'f'
		else:
			return None

	def getAbsDir(self):
		return os.path.dirname( self.getAbsFilePath() )

	def getAbsFilePath(self):
		if self.filePath:
			return AssetLibrary.get().getAbsProjectPath( self.filePath )
		else:
			return ''

	def getFileTime(self):
		return self.fileTime

	def getChildren(self):
		return self.children

	def getChildrenCount(self):
		return len(self.children)

	def _makeMetaDataFilePath( self ):
		if self.isFolder() and not self.isRemoteFile():
			dirname = self.getAbsFilePath()
			metaDir  = dirname + '/' + GII_ASSET_META_DIR
			metaPath = metaDir + '/' + '@this.meta'
		else:
			dirname  = self.getAbsDir()
			metaDir  = dirname + '/' +GII_ASSET_META_DIR
			metaPath = metaDir + '/' + self.getName() + '.meta'
		return ( metaDir, metaPath )

	def getMetaDataFilePath( self ):
		if self.isVirtual():
			p = self.findNonVirtualParent()
			if p : return p.getMetaDataFilePath()
			return None
		metaDir, metaPath = self._makeMetaDataFilePath()
		return metaPath

	def hasMetaData( self ):
		path = self.getMetaDataFilePath()
		if path:
			return os.path.isfile( path )
		else:
			return False

	def getMetaDataTable( self, createIfEmpty = True ):
		if self.isVirtual(): return None
		if self.metadata: return self.metadata
		metaPath = self.getMetaDataFilePath()
		if os.path.exists( metaPath ):
			data = JSONHelper.tryLoadJSON( metaPath )
			self.metadata = data or {}
			return self.metadata
		elif createIfEmpty:
			self.metadata = {}
			self.metaDataDirty = True
			return self.metadata
		return None

	def saveMetaDataTable( self ):
		if not self.metadata: return False
		if not self.metaDataDirty: return False
		metaDir, metaPath = self._makeMetaDataFilePath()
		if not os.path.exists( metaDir ):
			os.mkdir( metaDir )
		# text = json.dumps( self.metadata, indent = 2, sort_keys = True )
		data = self.metadata.copy()
		if os.path.isfile( metaPath ): #merge
			data0 = JSONHelper.tryLoadJSON( metaPath )
			if data0:
				for k, v in data.items():
					data0[ k ] = v
				data = data0
		text = JSONHelper.encodeJSON( data )
		fp = open( metaPath, 'w' )
		fp.write( text )
		fp.close()
		self.metaDataDirty = False
		return True

	def checkMetaDataUpdate( self ):
		metaPath = self.getMetaDataFilePath()
		if metaPath:
			if os.path.isfile( metaPath ):
				metaTimeNew = os.path.getmtime( metaPath )
				if self.metaTime < metaTimeNew:
					self.metaTime = metaTimeNew
					self.restoreMetaData()
			elif self.metaTime > 0: #metaDATA removed
				self.restoreMetaData()
				self.metaTime = 0

	def resetMetaData( self ):
		self.metadata = None
		self.metaDataDirty = False
		self.getMetaDataTable( True )
		self.restoreMetaData()

	def restoreMetaData( self ):
		if self.hasMetaData():
			self.tags = self.getMetaData( 'tags', [] )
		else:
			self.tags = []
		self.clearTagCache()

	def findNonVirtualParent( self ):
		node = self.getParent()
		while node:
			if not node.isVirtual(): return node
			node = node.getParent()
		return None

	def calcMetaFileHash( self ):
		filename = self.getMetaDataFilePath()
		with open( filename, 'r' ) as f:
			return hashlib.md5( f.read() ).hexdigest()

	def getMetaData( self, key, defaultValue = None ):
		if self.isVirtual():
			p = self.findNonVirtualParent()
			if p:
				profix = os.path.relpath( self.getNodePath(), p.getNodePath() )
				subkey = '%s@%s' % ( key, profix )
				return p.getMetaData( subkey, defaultValue )
		else:
			t = self.getMetaDataTable( False )
			if not isinstance( t, dict ): return defaultValue
			return t.get( key, defaultValue )

	def getInheritedMetaData( self, key, defaultValue = None ):
		n = self
		while n:
			v = n.getMetaData( key, None )
			if v != None: return v
			n = n.getParent()
		return defaultValue

	def setMetaData( self, key, value, **option ):
		if self.isVirtual():
			p = self.findNonVirtualParent()
			if p:
				profix = os.path.relpath( self.getNodePath(), p.getNodePath() )
				subkey = '%s@%s' % ( key, profix )
				return p.setMetaData( subkey, value, **option )
		else:
			t = self.getMetaDataTable( True )
			if not isinstance( t, dict ):
				raise Exception( 'can not find metadata table?' )

			if option.get( 'no_overwrite', False ) and key in t:
				return
			self.metaDataDirty = True
			v0 = t.get( key, None )
			if not deepEq( v0, value ): #modification checking
				t[ key ] = value
				if option.get( 'save', False ): self.saveMetaDataTable()
				if option.get( 'mark_modify', False ): self.markModified()

	def setNewMetaData( self, key, value, **option ):
		option[ 'no_overwrite' ] = True
		return self.setMetaData( key, value, **option )

	def addTag( self, tag, **option ):
		if tag in self.tags: return
		self.tags.append( tag )
		self.setMetaData( 'tags', self.tags, save = option.get( 'save', False ) )
		self.clearTagCache()

	def getTags( self ):
		return self.tags

	def getAllTags( self ):
		return self.getTagCache()

	def hasTag( self, tag, checkCache = True ):
		if not checkCache:
			return tag in self.tags
		else:
			cache = self.getTagCache()
			return tag in cache

	def removeTag( self, tag ):
		try:
			self.tags.remove( tag )
		except Exception as e:
			return False
		self.clearTagCache()
		return True

	def getTagString( self ):
		return ', '.join( self.getTags() )

	def getInheritedTagString( self ):
		return ', '.join( self.getInheritedTags() )

	def getTagCacheString( self ):
		return ', '.join( self.getTagCache() )

	def setTagString( self, src ):
		deprecated0 = 'deprecated' in self.tags
		self.tags = []
		self.clearTagCache()
		empty = True
		for part in [ x.strip() for x in src.split(',') ]:
			if len( part ) > 0:
				self.addTag( part )
				empty = False
		deprecated1 = 'deprecated' in self.tags
		if deprecated0 != deprecated1:
			self.updateUserDeprecated()

		if empty:
			self.setMetaData( 'tags', self.tags, save = False )
		self.saveMetaDataTable()

	def clearTagCache( self ):
		if self.tagCache:
			self.tagCache = None
			self.inheritedTags = None
			for child in self.children:
				child.clearTagCache()

	def getTagCache( self ):
		if not self.tagCache:
			self.updateTagCache()
		return self.tagCache

	def getTagCacheMap( self ):
		if not self.tagCache:
			self.updateTagCache()
		return self.tagCacheMap

	def getInheritedTags( self ):
		if not self.inheritedTags:
			self.updateTagCache()
		return self.inheritedTags

	def updateTagCache( self ): #collect tag from parent nodes
		inherited = {}
		collected = {}
		cache = []
		if self.parentNode:
			parentCache = self.parentNode.getTagCache()
			for tag in parentCache:
				inherited[ tag ] = True
				collected[ tag ] = True
			cache = parentCache[:]
		self.inheritedTags = list(inherited.keys())
		
		for tag in self.tags:
			collected[ tag ] = True
			if tag in cache: cache.remove( tag )
			cache.insert( 0, tag ) #put to front
		self.tagCache = cache
		self.tagCacheMap = collected

	def isInternalDeprecated( self ):
		return self.getProperty( 'deprecated', False )

	def isUserDeprecated( self ):
		return self.getProperty( 'user_deprecated', None )

	def setInternalDeprecated( self, deprecated = True ):
		self.setProperty( 'deprecated', deprecated )

	def isDeprecated( self ):
		return self.isInternalDeprecated() or self.isUserDeprecated()

	def updateUserDeprecated( self ):
		deprecated = 'deprecated' in self.tags #self deprecated
		if not deprecated:
			p = self.getParent()
			if p and p.isUserDeprecated():
				deprecated = True #parent deprecated

		if self.isUserDeprecated() == deprecated: return #no change, skip children update
		self.setProperty( 'user_deprecated', deprecated )
		for child in self.children:
			child.updateUserDeprecated()

	#WorkspaceData
	def getWorkspaceTable( self, createIfEmpty = True ):
		if self.workspaceState: return self.workspaceState
		name = makeMangledFilePath( self.getPath() )
		project = AssetLibrary.get().project
		path = project.getWorkspacePath( GII_ASSET_WORKSPACE_DIR + '/' + name )
		if os.path.exists( path ):
			data = JSONHelper.tryLoadJSON( path )
			self.workspaceState = data or {}			
			return self.workspaceState
		elif createIfEmpty:
			self.workspaceState = {}
			return self.workspaceState
		return None

	def saveWorkspaceTable( self ):
		if not self.workspaceState: return False
		name = makeMangledFilePath( self.getPath() )
		project = AssetLibrary.get().project
		path = project.getWorkspacePath( GII_ASSET_WORKSPACE_DIR + '/' + name )
		# text = json.dumps( self.workspaceState, indent = 2, sort_keys = True )
		text = JSONHelper.encodeJSON( self.workspaceState )
		fp = open( path, 'w' )
		fp.write( text )
		fp.close()
		return True

	def getWorkspaceData( self, key, defaultValue = None ):
		t = self.getWorkspaceTable( False )
		if not isinstance( t, dict ): return defaultValue
		return t.get( key, defaultValue )

	def setWorkspaceData( self, key, value, **option ):
		t = self.getWorkspaceTable()
		if not isinstance( t, dict ): return
		v0 = t.get( key, None )
		if v0 != value:
			t[ key ] = value
			if option.get( 'save', True ): self.saveWorkspaceTable()

	def setNewMetaData( self, key, value, **option ):
		option[ 'no_overwrite' ] = True
		return self.setMetaData( key, value, **option )

	#Cache
	def getCacheDir( self, name, **option ):
		option[ 'is_dir' ] = True
		return self.getCacheFile( name, **option )

	def getCacheFile( self, name, **option ):
		cacheFile = self.cacheFiles.get( name, None )
		if cacheFile: return cacheFile
		if option.get( 'affirm', True ):
			cacheFile = CacheManager.get().getCacheFile( self.getPath(), name, **option )
			self.cacheFiles[ name ] = cacheFile
			return cacheFile
		else:
			return None

	def getAbsCacheFile( self, name, **option ):
		path = self.getCacheFile( name, **option )
		if not path: return None
		return AssetLibrary.get().getAbsProjectPath( path )

	def clearCacheFiles( self ):
		self.cacheFiles = {}

	def checkCacheFiles( self ):
		for id, path in self.cacheFiles.items():
			fullpath = AssetLibrary.get().getAbsProjectPath( path )
			if not os.path.exists( fullpath ): return False
		return True

	def checkObjectFiles( self ):
		for id, path in self.objectFiles.items():
			fullpath = AssetLibrary.get().getAbsProjectPath( path )
			if not os.path.exists( fullpath ): return False
		return True

	def getObjectFile(self, name):
		return self.objectFiles.get( name, None )

	def setObjectFile(self, name, path):
		if not path:
			if name in self.objectFiles:
				del self.objectFiles[ name ]
		else:
			self.objectFiles[ name ] = path		

	def getAbsObjectFile( self, name ):
		path = self.getObjectFile( name )
		if not path: return None
		return AssetLibrary.get().getAbsProjectPath( path )

	def clearObjectFiles( self ):
		self.objectFiles = {}
		
	def edit(self):
		self.getManager().editAsset(self)

	def getProperty(self, name, defaultValue=None ):
		return self.properties.get(name, defaultValue)

	def setProperty(self, name, value):
		self.properties[ name ] = value

	def showInBrowser(self):
		if self.isVirtual():
			actualNode = self.findNonVirtualParent()
			if not actualNode: return
		else:
			actualNode = self
		path = actualNode.getAbsFilePath()
		if path:
			AssetUtils.showFileInBrowser(path)

	def openInSystem(self):
		path = self.getAbsFilePath()
		if path:
			AssetUtils.openFileInOS(path)

	def deleteFile( self ):
		manager = self.getManager()
		if manager:
			manager.deleteAssetFile( self )

	def _updateFileTime( self, mtime = None ):
		if self.isVirtual(): return
		try:
			self.fileTime = mtime or os.path.getmtime( self.getAbsFilePath() )
		except Exception as e:
			pass

	#just a shortcut for configuration type asset
	def loadAsJson(self):
		if self.isVirtual(): return None
		filepath = self.getAbsFilePath()

		fp = open(filepath , 'r')
		text = fp.read()
		fp.close()
		data = json.loads(text)

		return data

	def saveAsJson(self, data):
		if self.isVirtual(): return False
		filepath = self.getAbsFilePath()

		text = json.dumps( data, indent = 2, sort_keys = True )
		fp = open(filepath , 'w')
		fp.write(text)
		fp.close()

		self.markModified()
		return True


##----------------------------------------------------------------##
class AssetManager(object):	
	def getName(self):
		return 'asset_manager'

	def getVersion( self ):
		return 0

	def __lt__(self, other):
		return other.getPriority() < self.getPriority()

	def register( self ):
		AssetLibrary.get().registerAssetManager( self )

	def getPriority(self):
		return 0

	def acceptAsset( self, assetNode ):
		if assetNode.isVirtual():
			return self.acceptVirtualAsset( assetNode )
		else:
			return self.acceptAssetFile( assetNode.getAbsFilePath() )

	def acceptVirtualAsset( self, assetNode ):
		if assetNode.getManager() == self: return True
		return False

	def acceptAssetFile(self, filepath):
		return False

	def importAsset(self, assetNode, reload = False):
		return None
	
	def dropAsset( self, assetNode ):
		pass

	def cloneAsset( self, assetNode ):
		pass

	def deleteAssetFile( self, assetNode ):
		filepath = assetNode.getAbsFilePath()
		if os.path.isfile( filepath ):
			os.remove( filepath )
		elif os.path.isdir( filepath ):
			shutil.rmtree( filepath )

	#edit
	def editAsset(self, assetNode):
		assetNode.openInSystem()

	#modify
	def markModified( self, assetNode ):
		assetNode.modifyState = 'modified'
		for child in assetNode.getChildren():
			child.markModified()

	def getDependency( self, assetNode ):
		pass

	def onRegister( self ): #manager register
		pass

	def getMetaType( self ):
		return None

	def hasAssetThumbnail( self, assetNode ): #override this for thumnail
		return False

	def requestAssetThumbnail( self, assetNode, size, forced = False ):		
		if not self.hasAssetThumbnail( assetNode ): return None

		thumbnailPath = assetNode.getThumbnailPath( size )
		if not forced:
			if thumbnailPath and os.path.exists( thumbnailPath ): return thumbnailPath

		thumbnailPath = assetNode.getThumbnailPath( size, True )
		if self.buildAssetThumbnail( assetNode, thumbnailPath, size ):
			return thumbnailPath
		else:
			return None

	def buildAssetThumbnail( self, assetNode, targetPath, size ):
		return False

	def buildAssetSearchInfo( self, assetNode, **options ):
		info = {}
		uppercase =  options.get( 'uppercase', False )
		def _toUpper( v, convert ):
			if not convert: return v
			if isinstance( v, list ):
				return [ item.upper() for item in v ]
			else:
				return v.upper()
		info[ 'tag'  ] = _toUpper( assetNode.getTagCache() , uppercase )
		info[ 'type' ] = _toUpper( assetNode.getType() , uppercase )
		info[ 'name' ] = _toUpper( assetNode.getName() , uppercase )

		return info

	#deploy
	def getDefaultAssetDeployConfig( self, assetNode ):
		return {}

	def getAssetDeployConfig( self, assetNode ):
		default = self.getDefaultAssetDeployConfig( assetNode )
		def getConfig( configKey ):
			return assetNode.getInheritedMetaData( 'deploy_'+configKey, default.get( configKey, None ) )
		return {
			'policy'  : getConfig( 'policy' ),
			'package' : getConfig( 'package'),
		}

	#Process asset for deployment. eg.  Filepath replace, Extern file collection
	def deployAsset( self, assetNode, context ):
		context.addAssetObjectFiles( assetNode )


##----------------------------------------------------------------##
class RawAssetManager(AssetManager):	
	def getName(self):
		return 'raw'

	def getPriority( self ):
		return -1

	def acceptAssetFile(self, filepath):
		return True

	def importAsset(self, assetNode, reload = False ):
		path = os.path.realpath( assetNode.getAbsFilePath() )
		if os.path.isfile( path ): 
			assetNode.assetType = 'file'
		elif os.path.isdir( path ):
			assetNode.assetType = 'folder'
			assetNode.groupType = 'folder'
		return True

	def markModified(self, assetNode ):
		if assetNode.assetType == 'folder':
			pass
		assetNode.modifyState = 'modified'


##----------------------------------------------------------------##
class AssetCreator(object, metaclass=ABCMeta):
	@abstractmethod
	def getAssetType( self ):
		return 'name'

	@abstractmethod
	def getLabel( self ):
		return 'Label'

	def register( self ):
		return AssetLibrary.get().registerAssetCreator( self )

	#return asset path?
	def createAsset(self, name, contextNode, assetType):
		return False


##----------------------------------------------------------------##
class RemoteFileNode(object):
	def __init__( self ):
		self.targetAssetPath = False
		self.timestamp       = 0
		self.ruleFileHash    = ''
		self.ruleFileTime    = 0
		self.modifyState     = False
		self.remoteFileRule  = None
		self.remoteFileMetaTable = {}

	def getRuleFilePath( self ):
		name = os.path.basename( self.targetAssetPath )
		parentDir = os.path.dirname( self.targetAssetPath )
		rulePath  = parentDir + '/' + GII_REMOTE_DIR + '/' + name + '.remote'
		return rulePath

	def getAbsRuleFilePath( self ):
		return AssetLibrary.get().getAbsPath( self.getRuleFilePath() )

	def getRuleFileTime( self ):
		return 0

	def getTargetAssetPath( self ):
		return self.targetAssetPath

	def getAbsTargetAssetPath( self ):
		return AssetLibrary.get().getAbsPath( self.targetAssetPath )

	def getTargetAssetNode( self ):
		return AssetLibrary.get().getAssetNode( self.targetAssetPath )

	def getRemoteFileRule( self ):
		if not self.remoteFileRule:
			self.reloadRemoteFileRule()
		return self.remoteFileRule

	def calcRuleFileHash( self ):
		filename = self.getAbsRuleFilePath()
		with open( filename, 'rb' ) as f:
			return hashlib.md5( f.read() ).hexdigest()

	def isRuleFileModified( self ):
		f = self.getAbsRuleFilePath()
		mtime = os.path.getmtime( f )
		if mtime > self.ruleFileTime:
			if self.ruleFileHash == self.calcRuleFileHash(): #content is not updated
				atime = os.path.getatime( f )
				os.utime( f, (atime,self.ruleFileTime) )
				return False
			else:
				return True
		return False

	def isRemoteFileModified( self ):
		if self.isRuleFileModified():
			if not self.reloadRemoteFileRule( True ): return False
		rule = self.getRemoteFileRule()
		if not rule: return False
		return rule.checkModified( self.remoteFileMetaTable )

	def getFileList( self ):
		return list(self.remoteFileMetaTable.keys())

	def getSourceFileList( self, source = 'local' ):
		if self.isRuleFileModified():
			if not self.reloadRemoteFileRule( True ): return False
		rule = self.getRemoteFileRule()
		if not rule: return []
		info, contex = rule.getURL( source = source )
		result = []
		for entry in info:
			result.append( ( entry['url'], entry['target'] ) )
		return result

	def reloadRemoteFileRule( self, updateMTime = False ):
		path = self.getAbsRuleFilePath()
		rule = RemoteFile.RemoteFileRule()
		rule0 = self.remoteFileRule
		logging.info( 'loading remote file rule:' + path )
		if not os.path.isfile( path ): return False
		if rule.parseFile( path ):
			if rule0:
				rule0.stopWatch()
			self.remoteFileRule = rule
			rule.setUserData( self )
			if updateMTime:
				self.ruleFileTime = os.path.getmtime( path )
			rule.watch()
			return True
		return False

	def pull( self, **option ):
		if self.isRuleFileModified():
			if not self.reloadRemoteFileRule( True ): return False
		rule = self.getRemoteFileRule()
		if not rule: return False
		self.ruleFileHash = self.calcRuleFileHash()
		if rule.pull( self.getAbsTargetAssetPath(), self.remoteFileMetaTable, **option ):
			self.modifyState = False
			return True
		else:
			return False

	def deleteLocalAsset( self ):
		node = self.getTargetAssetNode()
		if node:
			node.deleteFile()
			return True
		return False

	def startWatch( self ):
		rule = self.getRemoteFileRule()
		if rule: rule.watch()

	def stopWatch( self ):
		rule = self.getRemoteFileRule()
		if rule: rule.stopWatch()

##----------------------------------------------------------------##
class AssetRootNode( AssetNode ):
	def getName( self ):
		return 'asset'


##----------------------------------------------------------------##
class AssetLibrary(object):
	"""docstring for AssetLibrary"""
	_singleton=None

	@staticmethod
	def get():
		return AssetLibrary._singleton

	def __init__(self, project):
		assert not AssetLibrary._singleton
		AssetLibrary._singleton=self
		self.project         = project
		self.projectScanScheduled = False
		self.cacheScanned    = False

		self.assetTable      = {}
		self.assetManagers   = []
		self.assetCreators   = []
		self.assetManagerMap = {}

		self.previousAssetData = None

		self.remoteFileTable = {}

		self.rawAssetManager = RawAssetManager()
		
		self.rootPath        = None

		self.assetIconMap    = {}

		self.ignoreFilePatterns = [
			'\.git',
			'\.assetmeta',
			'\.remote',
			'^\..*',
			'.*\.pyo$',
			'.*\.pyc$'
		]
		self.updateIgnorePatternCache()
		self.changedFiles = {}

	def load( self, rootPath, rootAbsPath, projectAbsPath, configPath ):
		#load asset
		self.rootPath       = rootPath
		self.rootAbsPath    = rootAbsPath
		self.projectAbsPath = projectAbsPath
		self.assetIndexPath = configPath + '/' + GII_ASSET_INDEX_PATH
		self.assetIndexOutputPath = configPath + '/' + GII_ASSET_INDEX_OUTPUT_PATH
		self.remoteIndexPath = configPath + '/' + GII_REMOTE_FILE_INDEX_PATH
		self.rootNode       = AssetRootNode( '', 'folder', filePath = self.rootPath )
		self.affirmAssetIndexOutput()

	def save( self ):
		self.saveRemoteFileTable()
		self.saveAssetTable()
		self.affirmAssetIndexOutput()

	def affirmAssetIndexOutput( self ):
		if not os.path.isfile( self.assetIndexPath ): 
			return
		elif not os.path.isfile( self.assetIndexOutputPath ):
			self.saveAssetIndexOutput()
		elif os.path.getmtime( self.assetIndexPath ) > os.path.getmtime( self.assetIndexOutputPath ):
			self.saveAssetIndexOutput()

	def saveAssetIndexOutput( self ):
		try:
			src = self.assetIndexPath
			dst = self.assetIndexOutputPath
			shutil.copyfile( src, dst )
			shutil.copyfile( src + '.packed', dst + '.packed' )
		except Exception as e:
			return False
		return True

	def reset( self ):
		signals.emit( 'asset.reset' )
		self.unregisterAssetNode( self.rootNode )
		self.scanProject( full=True )

	def getRootNode(self):
		return self.rootNode

	#Path
	def getAbsPath( self, path ):
		return self.rootAbsPath + '/' + path

	def getAbsProjectPath( self, path ):
		return self.projectAbsPath + '/' + path

	def getRelPath( self, path ):
		path = os.path.abspath( path )
		return os.path.relpath( path, self.rootAbsPath )

	#access
	def getAllAssets( self ):
		return list(self.assetTable.values())

	def getAssetTable( self ):
		return self.assetTable

	def iterAssets( self ):
		return self.assetTable.values()

	def hasAssetNode(self, nodePath):
		if not nodePath: return False
		return not self.getAssetNode( nodePath ) is None

	def getAssetNode(self, nodePath):
		if not nodePath: return self.rootNode
		return self.assetTable.get(nodePath, None)

	def markAssetNodeModified(self, nodePath):
		if not nodePath: return False
		node = self.getAssetNode( nodePath )
		if node:
			node.markModified()
			self.scheduleScanProject()
		else:
			logging.warn( 'no asset marked modified:' + nodePath )

	def enumerateAsset( self, patterns = None, **options ):
		noVirtualNode = options.get( 'no_virtual', False )
		includeDeprecatedNode = options.get( 'include_deprecated', False )
		result = []
		subset = options.get( 'subset', iter(list(self.assetTable.values())) )
		
		#filter
		refined = []
		for node in subset:
			if ( noVirtualNode and node.isVirtual() ) : continue
			if ( node.hasTag( 'deprecated' ) and ( not includeDeprecatedNode )  ) : continue
			refined.append( node )
		subset = refined

		#filter Metatype
		metaType = options.get( 'meta_type', None )

		if metaType:
			refined = []
			for node in subset:
				if node.getMetaType() == metaType:
					refined.append( node )
			subset = refined

		if not patterns:
			return subset

		#Filter patterns
		if isinstance( patterns, str ):
			patterns = patterns.split(';')

		matchPatterns = []
		for p in patterns:
			pattern = re.compile( p )
			matchPatterns.append( pattern )

		for node in subset:
			for matchPattern in matchPatterns:
				target = node.getType()
				mo = matchPattern.match( node.getType() )
				if not mo: continue
				if mo.end() < len( node.getType() ) - 1 : continue
				result.append(node)
				break
		return result

	def searchAsset( self, citeria, **options ):
		if isinstance( citeria, TagMatch.TagMatchRule	):
			rule = citeria
		elif isinstance( citeria, str ):
			rule = TagMatch.parseTagMatch( citeria, **options )
		else:
			rule = None
		if not rule: return []
		result = []
		for node in list(self.assetTable.values()):
			info = node.buildSearchInfo( **options )
			if not info: continue
			if rule.evaluate( info ):
				result.append( node )
		return result

	#tools
	def addFileIgnorePattern( self, pattern ):
		if pattern in self.ignoreFilePatterns: return
		self.ignoreFilePatterns.append( pattern )
		self.updateIgnorePatternCache()

	def removeFileIgnorePattern( self, pattern ):
		if pattern in self.ignoreFilePatterns:
			idx = self.ignoreFilePatterns.index( pattern )
			ignoreFilePattern.pop( idx )
			self.updateIgnorePatternCache()

	def updateIgnorePatternCache( self ):
		cache = []
		for pattern in self.ignoreFilePatterns:
			compiled = re.compile( pattern )
			if compiled :
				cache.append( compiled )
		self.ignoreFilePatternCache = cache

	def checkFileIgnorable(self, name):
		for compiledPattern in self.ignoreFilePatternCache:
			if compiledPattern.match( name ):
				return True
		return False

	def fixPath( self, path ):
		path = path.replace( '\\', '/' ) #for windows
		if path.startswith('./'): path = path[2:]
		return path

	#Assetmanagers
	def registerAssetManager( self, manager, **option ):
		logging.info( 'registering asset manager:'+manager.getName() )

		override = False
		name = manager.getName()
		mgr0 = self.assetManagerMap.get( name, None )
		if mgr0:
			if not option.get( 'override', False ): 
				raise AssetException('AssetManager name conflict %s'%manager.getName())
			else:
				override = True
				self.assetManagers.remove( mgr0 )
				logging.info( 'override asset manager:' + manager.getName() )

		self.assetManagerMap[ name ] = manager

		idx = None
		priority = manager.getPriority()
		for p in self.assetManagers:
			if p == manager:
				raise AssetException('Duplicated AssetManager %s'%manager.getName())
			if priority >= p.getPriority():
				idx = self.assetManagers.index( p )
				break

		if idx != None:
			self.assetManagers.insert(idx, manager)
		else:
			self.assetManagers.append(manager)

		manager.onRegister()
		return manager

	def registerAssetCreator(self, creator):
		self.assetCreators.append( creator )

	def getAssetManager(self, name, allowRawManager = False ):
		mgr = self.assetManagerMap.get( name, None )
		if mgr: return mgr
		return allowRawManager and self.rawAssetManager or None

	def getAssetCreator( self, assetType ):
		for creator in self.assetCreators:
			if creator.getAssetType() == assetType:
				return creator
		return None

	def getAssetIcon( self, assetType ):
		return self.assetIconMap.get( assetType, assetType )

	def setAssetIcon( self, assetType, iconName ):
		self.assetIconMap[ assetType ] = iconName

	def registerAssetNode( self, node ):
		path = node.getNodePath()
		logging.info( 'register: %s' % repr(node) )
		if path in self.assetTable:
			raise Exception( 'unclean path: %s', path)
		self.assetTable[path] = node

		signals.emit( 'asset.register', node )

		for child in node.getChildren():
			self.registerAssetNode( child )
		node.restoreMetaData()
		return node

	def unregisterAssetNode(self, oldnode):
		assert oldnode
		logging.info( 'unregister: %s' % repr(oldnode) )
		
		for child in oldnode.getChildren()[:]:
			self.unregisterAssetNode(child)

		if oldnode != self.rootNode:
			oldnode.getManager().dropAsset( oldnode )
			signals.emitNow( 'asset.unregister', oldnode )
			if oldnode.parentNode: 
				oldnode.parentNode.removeChild(oldnode)
				oldnode.parentNode = None
			path = oldnode.getNodePath()
			if path in self.assetTable:
				del self.assetTable[path]

	def initAssetNode( self, path, option = None, **kwargs ):
		#fix path
		absFilePath = os.path.abspath( self.rootAbsPath + '/' + path )
		fileTime = os.path.getmtime(absFilePath)
		filePath = self.rootPath + '/' + path
		
		#if inside bundle, skip
		if self._getParentBundle( path ): return None

		assert not self.getAssetNode( path )
		#create a common asset node first
		parentNode = self.getAssetNode( os.path.dirname( path ) )
		if not parentNode:
			logging.error( 'no parent node found:' + os.path.dirname( path ) )
			return None

		node = AssetNode( 
			path,
			os.path.isfile(absFilePath) and 'file' or 'folder', 
			fileTime = fileTime,
			filePath = filePath,
			**kwargs )
		node.fileType = node.detectFileType()
		node.setManager( self.rawAssetManager )
		self.registerAssetNode( node )
		parentNode.addChild(node)	
		node.markModified()

		return node

	def reimportAll(self):
		#TODO:should this be done by a asset index rebuilding (by restarting editor)?
		pass

	def importModifiedAssets( self ):
		importCount = 0 
		t0 = time.time()
		def _notifyVirtualNodeModified( node ):
			if child in node.getChildren():
				_notifyVirtualNodeImported( child )
			if not node.modifyState == 'ignored':
				signals.emitNow( 'asset.modified', node )

		def _notifyVirtualNodeImported( node ):
			if child in node.getChildren():
				_notifyVirtualNodeImported( child )
			if not node.modifyState == 'ignored':
				signals.emitNow( 'asset.imported', node )
			node.modifyState = None

		def _ignoreBundleChildrenNode( node ):
			for child in node.getChildren()[:]:
				if not child.isVirtual():
					_ignoreBundleChildrenNode( child )
					child.modifyState = 'ignored'
					self.unregisterAssetNode( child )

		def _markVirtualChildrenRemoving( node, removingAssets ):			
			for child in node.getChildren()[:]:
				if child.isVirtual():
					_markVirtualChildrenRemoving( child, removingAssets )
					child.modifyState = 'removing'
					removingAssets[ child ] = True

		#collect modified state
		removingAssets = {}
		modifiedAssetList = []
		for node in list(self.assetTable.values()):
			if not node.modifyState: continue
			if not node.isVirtual():
				if node.modifyState == 'modified': node.clearObjectFiles()
				modifiedAssetList.append( node )
				logging.info( 'asset modified: {0}'.format( node.getNodePath() ) )

		if not modifiedAssetList: return False
		modifiedAssetList = sorted( 
				modifiedAssetList, key = lambda node: node.getPathDepth()
			)
		done = []
		rest = []
		err  = []
		#try importing with each asset manager, in priority order
		for manager in self.assetManagers:
			if not modifiedAssetList: break
			for node in modifiedAssetList:
				if node.modifyState in ( 'removed', 'ignored' ) :
					done.append( node )
					continue
				if not node.modifyState: #might get imported as a sub asset 
					done.append( node )
					continue
				if not manager.acceptAsset( node ):
					rest.append( node )
					continue
				
				isNew = node.modifyState == 'new'
				if not isNew:
					_markVirtualChildrenRemoving( node, removingAssets )

				if node.getManager() != manager: 
					node.setManager( manager )

				succ = False
				try:
					succ = manager.importAsset( node, reload = not isNew )
				except Exception as e:
					logging.exception( e )
					succ = False

				if succ != False:
					logging.info( 'assets imported: {0}'.format( node.getNodePath() ) )
					node.modifyState  =  False
					node.managerVersion = manager.getVersion()
					done.append( node )
					if node.isBundle():
						node._updateFileTime( self._getBundleMTime( node.getAbsFilePath() ) )					
					else:
						node._updateFileTime()
				else:
					logging.error( 'failed importing asset: {0}'.format( node.getNodePath() ) )
					node.modifyState = 'error'
					done.append( node )

				if not isNew:
					signals.emitNow( 'asset.modified',  node )
					# if node.isBundle():
					for child in node.children:
						if child.isVirtual():
							_notifyVirtualNodeModified( child )

				if node.isBundle():
					_ignoreBundleChildrenNode( node )

				importCount += 1
				if importCount > 200:
					importCount = 0
					self.saveAssetTable()
					CacheManager.get().save()

			for node in done:				
				if node.modifyState == 'ignored': continue
				if node.modifyState == 'error': pass
				if node.isBundle():
					node._updateFileTime( self._getBundleMTime( node.getAbsFilePath() ) )					
				else:
					node._updateFileTime()

			modifiedAssetList = rest
			rest = []

		for node in modifiedAssetList: #nodes without manager
			if node.isBundle():
				node._updateFileTime( self._getBundleMTime( node.getAbsFilePath() ) )					
			else:
				node._updateFileTime()
			node.modifyState = None

		for node in list(removingAssets.keys()):
			if node.modifyState == 'removing':
				self.unregisterAssetNode( node )
				node.modifyState = 'removed'

		#end of for
		signals.dispatchAll()
		signals.emitNow( 'asset.post_import_all' )
		for node in done:				
			if node.modifyState == 'ignored': continue
			signals.emitNow( 'asset.imported', node )
			for child in node.children:
				if child.isVirtual():
					_notifyVirtualNodeImported( child )
			# if node.isReady():
			# 	signals.emitNow( 'asset.ready', node )
		signals.dispatchAll()
		logging.info( 'modified assets imported: %.3f' % ( time.time() - t0 ) )
		signals.emitNow( 'asset.imported_all' )
		return True

	def scanSingleRemoteFile( self, node ):
		remoteNode = self.getRemoteFileNode( node.getPath() )
		if remoteNode:
			if remoteNode.isRemoteFileModified():
				remoteNode.modifyState = 'updated'
				remoteNode.pull()
				self.saveRemoteFileTable()

	def scanRemoteFiles( self, scanRemoteTimestamp = True ):
		for node in list(self.remoteFileTable.values()):
			node.modifyState = None
		modified  = []
		removing  = []
		newnodes  = []
		updated   = []
		for currentDir, dirs, files in os.walk( str(self.rootAbsPath) ):
			if os.path.basename( currentDir ) != GII_REMOTE_DIR : continue
			parentDir = os.path.dirname( currentDir )
			parentRelDir = os.path.relpath( parentDir, self.rootAbsPath )
			for filename in files:
				name, ext = os.path.splitext( filename )
				if ext != GII_REMOTE_DIR: continue
				absRulePath = currentDir + '/' + filename
				nodePath = self.fixPath( parentRelDir + '/' + name )
				remoteNode = self.getRemoteFileNode( nodePath )
				if remoteNode:
					if remoteNode.isRuleFileModified():
						remoteNode.modifyState = 'modified'
						modified.append( remoteNode )
					elif scanRemoteTimestamp and remoteNode.isRemoteFileModified():
						remoteNode.modifyState = 'updated'
						updated.append( remoteNode )
					else:
						remoteNode.modifyState = False
				else:
					remoteNode = RemoteFileNode()
					remoteNode.targetAssetPath = nodePath
					remoteNode.modifyState = 'new'
					self.remoteFileTable[ nodePath ] = remoteNode
					newnodes.append( remoteNode )

		for node in self.remoteFileTable.values():
			if node.modifyState == None:
				node.modifyState = 'removed'
				removing.append( node )

		for removedRemoteNode in removing:
			removedRemoteNode.stopWatch()
			removedRemoteNode.deleteLocalAsset()
			del self.remoteFileTable[ removedRemoteNode.targetAssetPath ]

		for newNode in newnodes:
			newNode.pull()

		for modifiedRemoteNode in modified:
			modifiedRemoteNode.pull()

		for updatedNode in updated:
			updatedNode.pull()
		
		self.saveRemoteFileTable()

	def getRemoteFileNode( self, nodePath ):
		return self.remoteFileTable.get( nodePath, None )

	def createRemoteFile( self, contextNode, filename ):
		if contextNode.getType() != 'folder': return False
		p = contextNode.getAbsFilePath()
		if not _affirmPath( p +'/' + GII_REMOTE_DIR ): return False
		remoteFileName = filename + '.remote'
		remoteFilePath = p + '/' + GII_REMOTE_DIR + '/' + remoteFileName
		fp = open( remoteFilePath, 'w' )
		empty = '//Remote rule file\n//' + filename 
		fp.write( empty )
		fp.close()
		return remoteFilePath

	def scheduleScanProject( self ):
		self.projectScanScheduled = True

	def tryScanProject( self, **option ):
		if self.projectScanScheduled:
			self.scanProject( **option )
	
	#file watcher
	def onFileMoved( self, path, newpath ):
		self.changedFiles[ path ] = 'removed'
		self.changedFiles[ newpath ] = 'new'
		self.scheduleScanProject()

	def onFileCreated( self, path ):
		self.changedFiles[ path ] = 'new'
		self.scheduleScanProject()

	def onFileModified( self, path ):
		self.changedFiles[ path ] = 'modified'
		self.scheduleScanProject()

	def onFileDeleted( self, path ):
		self.changedFiles[ path ] = 'removed'
		self.scheduleScanProject()

	def onMetaChanged( self, path ):
		path = self.getRelPath( path )
		mo = metaPattern.match( path )
		if not mo:
			logging.warning( 'invalid asset meta path: %s', path )
			return False
		assetPath = mo.group(1) + mo.group(2)
		if mo.group(2) == '@this':
			assetPath = os.path.dirname( assetPath )
		node = self.getAssetNode( assetPath )
		if not node:
			logging.info( 'no asset node for meta: %s', assetPath )
			return False
		logging.info( 'reset meta: %s', assetPath )
		node.resetMetaData()
		return True

	#Library
	def _fullScan( self, **option ): #scan 
		self.scanRemoteFiles( False )
		changed = False
		self.changedFiles = {}
		logging.info('full scan project in:' + self.rootAbsPath )
		#scan meta files first ( will be used in asset importing )
		#TODO

		#check missing asset
		for assetPath, node in self.assetTable.copy().items():
			if assetPath not in self.assetTable: #already removed(as child of removed node)
				continue
			#check parentnode
			if not node.getParent():
				self.unregisterAssetNode( node )
				continue

			if node.isVirtual(): #don't check virtual node's file
				continue

			filePath = node.getAbsFilePath()
			
			#file deleted
			if not os.path.exists( filePath ):
				node.modifyState = 'removed'
				self.unregisterAssetNode( node )
				changed = True
				continue

			#file become ignored
			if self.checkFileIgnorable( node.getFilePath() ):
				node.modifyState = 'ignored'
				self.unregisterAssetNode( node )
				changed = True
				continue
			
		#check new asset
		for currentDir, dirs, files in os.walk( str(self.rootAbsPath) ):
			relDir = os.path.relpath( currentDir, self.rootAbsPath )

			for filename in files:
				if self.checkFileIgnorable( filename ):
					continue
				
				nodePath = self.fixPath( relDir + '/' + filename )
				absPath  = self.getAbsPath( nodePath )
				if self.checkFileIgnorable( nodePath ):
					continue

				mtime    = os.path.getmtime( absPath )
				bundle   = self._getParentBundle( nodePath )

				if bundle:
					if mtime > bundle.getFileTime():
						bundle.markModified()
					if not bundle.checkObjectFiles():
						bundle.markModified()
					if not bundle.checkManagerVersion():
						bundle.markModified()
				else:
					if not self.getAssetNode( nodePath ): #new
						self.initAssetNode( nodePath )
					else:
						node = self.getAssetNode( nodePath ) #modified
						if mtime > node.getFileTime():
							node.markModified()
						if not node.checkObjectFiles():
							node.markModified()
						if not node.checkManagerVersion():
							node.markModified()
						if node.getFileType() != 'f': #was not a actual file?
							node.markModified()
							node.fileType = node.detectFileType()

			dirs2 = dirs[:]
			for dirname in dirs2:
				if self.checkFileIgnorable(dirname):
					dirs.pop(dirs.index(dirname)) #skip walk this
					continue
				nodePath = self.fixPath( relDir + '/' + dirname )

				if self.checkFileIgnorable( nodePath ):
					dirs.pop(dirs.index(dirname)) #skip walk this
					continue

				node = self.getAssetNode( nodePath ) 
				if not node:
					self.initAssetNode( nodePath )
				else:
					if node.getFileType() != 'd': #was not a folder?
						node.markModified()
						node.fileType = node.detectFileType()

		return changed

	def _partialScan( self, **option ):
		#only check changed Files
		self.scanRemoteFiles( False )
		changed = False
		changedFiles = self.changedFiles
		self.changedFiles = {}

		logging.info('partial scanning:')
		for path, info in changedFiles.items():
			logging.info( '   changed file: %s -> %s' % ( path, info ) )
		
		changedAssets = {}
		#convert file info into asset info
		for path, info in changedFiles.items():
			if self.checkFileIgnorable( path ):
					continue
			relPath = os.path.relpath( path, self.rootAbsPath )
			nodePath = self.fixPath( relPath )

			if info == 'new' and os.path.exists( path ) :
				if not self.getAssetNode( nodePath ): #new
					changedAssets[ nodePath ] = 'new'
				else:
					changedAssets[ nodePath ] = 'modified'

			else:
				node = self.assetTable.get( nodePath, None )
				if not node: #try bundle
					bundle   = self._getParentBundle( nodePath )
					if bundle and not changedAssets.get( bundle.getNodePath(), None ) :
						changedAssets[ bundle.getNodePath() ] = 'modified'
				else:
					if info == 'removed' and ( not os.path.exists( path ) ):
						changedAssets[ nodePath ] = 'removed'
					else:
						changedAssets[ nodePath ] = 'modified'

		changeQueue = []
		for nodePath, info in changedAssets.items():
			changeQueue.append( (nodePath, info) )
		changeQueue = sorted( changeQueue, key = lambda entry: entry[0] )
		for entry in changeQueue:
			nodePath, info = entry
			if info == 'new':
				self.initAssetNode( nodePath )

			elif info == 'removed':
				node = self.getAssetNode( nodePath )
				if node: 
					node.modifyState = 'removed'
					self.unregisterAssetNode( node )

			elif info == 'modified':
				node = self.getAssetNode( nodePath )
				node.markModified()

		if changedAssets:	changed = True
		return changed


	def scanProject( self, **option ): #scan 
		logging.info( '=================' )
		logging.info( 'scanning asset' )
		t0 = time.time()
		
		fullScan = option.get( 'full', False )

		if fullScan:
			changed = self._fullScan( **option )
		else:
			changed = self._fullScan( **option )
			# changed = self._partialScan( **option )

		imported = self.importModifiedAssets()
		if changed or imported:
			self.saveAssetTable()
			CacheManager.get().save()
		else:
			logging.info( 'no asset update' )

		elapsed = time.time() - t0
		logging.info( 'done scanning project:%.3f' % elapsed )
		logging.info( '=================' )
		self.projectScanScheduled = False

	
	def buildProject( self ):
		pass

	def loadRemoteFileTable( self ):
		logging.info( 'loading remote table from:' + self.remoteIndexPath )
		RemoteFile.RemoteFileManager.get().init()
		
		if not os.path.exists( self.remoteIndexPath ): return
		dataTable = JSONHelper.tryLoadJSON( self.remoteIndexPath )

		if not dataTable: return False
		remoteFileTable={}
		
		for path, data in dataTable.items():
			node = RemoteFileNode()
			node.timestamp           = data.get( 'timestamp', 0 )
			node.ruleFileTime        = data.get( 'ruleFileTime', 0 )
			node.ruleFileHash        = data.get( 'ruleFileHash', '' )
			node.modifyState         = data.get( 'modifyState', False )
			node.targetAssetPath     = data.get( 'assetPath', path )
			node.remoteFileMetaTable = data.get( 'remoteFileMeta', {} )
			remoteFileTable[ path ]  = node
			node.startWatch()

		self.remoteFileTable = remoteFileTable

		logging.info("remote table loaded")
		return True

	def saveRemoteFileTable( self, **option ):
		t0 = time.time()
		outputPath = option.get( 'path', self.remoteIndexPath )		
		output = {}
		for path, node in self.remoteFileTable.items():
			item = {}
			output[ path ]=item
			#common
			item['assetPath']      = node.targetAssetPath
			item['timestamp']      = node.timestamp
			item['ruleFileTime']   = node.ruleFileTime
			item['ruleFileHash']   = node.ruleFileHash
			item['modifyState']    = node.modifyState
			item['remoteFileMeta'] = node.remoteFileMetaTable

		if not JSONHelper.trySaveJSON( output, outputPath, 'remote index' ):
			return False
		logging.info( 'remote table saved: %.3f' % ( time.time() - t0 ) )
		return True	

	def loadAssetTable(self):

		logging.info( 'loading asset table from:' + self.assetIndexPath )
		
		if not os.path.exists( self.assetIndexPath ): return
		dataTable = JSONHelper.tryLoadJSON( self.assetIndexPath )

		if not dataTable: return False
		
		assetTable={}

		for path,data in dataTable.items():
			node = AssetNode(path, data.get('type'), 
					filePath = data.get( 'filePath', path ),
					fileTime = data.get( 'fileTime', 0 )
				)
			node.deployState  = data.get('deploy', None)
			node.groupType    = data.get( 'groupType', None )
			node.cacheFiles   = data.get('cacheFiles', {})
			node.objectFiles  = data.get('objectFiles', {})
			node.properties   = data.get('properties', {}) 
			node.modifyState  =	data.get('modifyState' ,  False )
			node.managerVersion = data.get('managerVersion', 0)
			
			assetTable[path]  = node
			node.managerName  = data.get('manager')
			node.tags         = data.get('tags',[])
			node.tagCache     = None
			if node.groupType == None:
				if node.isType( 'folder' ):
					node.groupType = 'folder'

			fileType = data.get( 'fileType', None )
			if not fileType:
				node.fileType = node.detectFileType()
			else:
				node.fileType = fileType
			
		#relink parent/dependency
		for path, node in assetTable.items():
			ppath = os.path.dirname(path)
			if not ppath:
				pnode = self.rootNode
			else:
				pnode = assetTable.get(ppath,None)
			if not pnode:
				continue
			pnode.addChild(node)
			data = dataTable[path]

			for key, dpath in data.get( 'dependency', {} ).items():
				dnode = assetTable.get( dpath, None )
				if not dnode:
					logging.warn('missing dependency asset node', dpath )
					node.markModified()
				else:
					node.addDependency( key, dnode )

			#update updated metadata
			node.metaTime         = data.get('metaTime',0)
			node.checkMetaDataUpdate()

		self.assetTable=assetTable
		logging.info("asset library loaded")
		self.getRootNode().updateUserDeprecated()

	def saveAssetTable( self, **option ):
		t0 = time.time()
		logging.info( 'saving asset table' )
		signals.emitNow( 'asset.index.pre_save' )
		outputPath = option.get( 'path', self.assetIndexPath )		
		deployContext  = option.get( 'deploy_context',  False )
		mode = option.get( 'mode', 'editor' )
		deploying = mode == 'deploy'

		mapping = deployContext and deployContext.fileMapping
		table = {}
		for path, node in self.assetTable.items():
			item = {}
			table[ path ]=item
			#common
			item['type']          = node.getType()
			item['groupType']     = node.getGroupType()
			item['filePath']      = node.getFilePath() or False
			item['fileType']      = node.getFileType()
			item['tags']          = node.getTags()
			item['properties']    = node.properties
			item['managerVersion'] = node.managerVersion

			item['dependency']  = node.dependency
			item['fileTime']    = node.getFileTime()

			#for deploy
			if deploying:
				if mapping:
					mapped = {}
					for key, path in node.objectFiles.items():
						mapped[ key ] = mapping.get( path, path )
					item['objectFiles'] = mapped
				else:
					item['objectFiles'] = node.objectFiles
				item['deployMeta'] = deployContext.getAssetDeployMeta( node )
			
			#for non deploy
			if not deploying:
				item['objectFiles'] = node.objectFiles
				item['metaTime']    = node.metaTime
				
				item['manager']     = node.managerName
				item['deploy']      = node.deployState
				item['modifyState'] = node.modifyState
				#mark cache files
				cacheFiles = {}
				for name, cacheFile in node.cacheFiles.items():
					if CacheManager.get().touchCacheFile( cacheFile ): cacheFiles[ name ] = cacheFile
				node.cacheFiles = cacheFiles
				item['cacheFiles']  = node.cacheFiles
				node.saveMetaDataTable()	

		t1 = time.time()
		logging.info( 'asset data ready: %.3f' % ( t1 - t0 ) )
		if not JSONHelper.trySaveJSON( table, outputPath, 'asset index' ):
			return False

		t2 = time.time()
		logging.info( 'written asset table: %.3f' % ( t2 - t1 ) )

		with open( outputPath + '.packed', 'wb' ) as fp:
			fp.write( msgpack.packb( table ) )

		t3 = time.time()
		logging.info( 'saved asset table msgpack: %.3f' % ( t3 - t2 ) )

		logging.info( 'asset table saved' )
		signals.emitNow( 'asset.index.save' )
		self.previousAssetData = table
		return True	

	def clearFreeMetaData( self ):
		#check new asset
		for currentDir, dirs, files in os.walk( str(self.rootPath) ):
			dirs2=dirs[:]
			for dirname in dirs2:
				if self.checkFileIgnorable(dirname):
					dirs.pop(dirs.index(dirname)) #skip ignored files
					continue

			relDir  = os.path.relpath(currentDir, self.rootPath)
			metaDir = currentDir + '/' + GII_ASSET_META_DIR

			if os.path.exists( metaDir ):
				for filename in os.listdir( metaDir ):
					if not filename.endswith('.meta'): continue
					if filename == '@this.meta' :continue
					assetName = filename [:-5] #remove '.meta'
					assetPath = currentDir + '/' +assetName
					if ( not os.path.exists( assetPath ) ):
						metaPath = metaDir + '/' +filename
						logging.info( 'remove metadata: %s' % metaPath )
						os.remove( metaPath )
				#TODO: remove meta folder if it's empty

	def restoreAllMetaData( self ):
		for node in self.iterAssets():
			node.restoreMetaData()

	def _getParentBundle ( self, path ):
		while True:
			path1 = os.path.dirname(path)
			if not path1 or path1 == path: return None
			path  = path1
			pnode = self.getAssetNode( path )
			if pnode and pnode.isBundle(): return pnode

	def _getBundleMTime( self, path ):
		mtime = 0
		for currentDir, dirs, files in os.walk( path ):
			for filename in files:
				if self.checkFileIgnorable(filename):
					continue
				mtime1 = os.path.getmtime( currentDir + '/' + filename )
				if mtime1 > mtime:
					mtime = mtime1
			dirs2 = dirs[:]
			for dirname in dirs2:
				if self.checkFileIgnorable(dirname):
					dirs.pop(dirs.index(dirname)) #skip walk this
					continue
				mtime1 = os.path.getmtime( currentDir + '/' + dirname )
				if mtime1 > mtime:
					mtime = mtime1
		return mtime



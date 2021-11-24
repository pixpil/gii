import os
import os.path
import logging
from . import JSONHelper
import shutil

from .tmpfile import TempDir
from .helpers import makeMangledFilePath

_GII_CACHE_PATH       =  'cache'
_GII_CACHE_INDEX_PATH =  'cache_index.json'
_GII_CACHE_CATEGORY_THUMBNAIL   =  '_thumbnails'


##----------------------------------------------------------------##
class CacheManager(object):
	_singleton = None
	
	@staticmethod
	def get():
		return CacheManager._singleton

	def __init__( self ):
		assert not CacheManager._singleton
		CacheManager._singleton = self

		super(CacheManager, self).__init__()
		self.cachePath      = None
		self.cacheAbsPath   = None
		self.cacheIndexPath = None
		self.cacheFileTable = {} 
		self.categories = {}

	def init( self, basePath, absBasePath ):
		self.cachePath      = basePath + '/' + _GII_CACHE_PATH
		self.cacheAbsPath   = absBasePath + '/' + _GII_CACHE_PATH
		self.cacheIndexPath = absBasePath + '/' + _GII_CACHE_INDEX_PATH
		self.affirmFolders()
		return True

	def affirmFolders( self ):
		#check and create cache path exists ( for safety )
		if not os.path.exists( self.cacheAbsPath ):
			os.mkdir( self.cacheAbsPath )
		self.affirmCategory( 'thumbnail', _GII_CACHE_CATEGORY_THUMBNAIL )

	def affirmCategory( self, id, subPath ):
		self.categories[ id ] = subPath
		absPath = self.cacheAbsPath + '/' + subPath
		if not os.path.exists( absPath ):
			os.mkdir( absPath )

	def load( self, basePath, absBasePath ):
		self.cachePath      = basePath + '/' + _GII_CACHE_PATH
		self.cacheAbsPath   = absBasePath + '/' + _GII_CACHE_PATH
		self.cacheIndexPath = absBasePath + '/' + _GII_CACHE_INDEX_PATH
		self.affirmFolders()
		#load cache file index
		self.cacheFileTable = JSONHelper.tryLoadJSON( self.cacheIndexPath ) or {}
		for path, node in self.cacheFileTable.items():
			node[ 'touched' ] = False

		return True

	def save( self ):
		#save cache index
		JSONHelper.trySaveJSON( self.cacheFileTable, self.cacheIndexPath, 'cache index' )		

	def touchCacheFile( self, cacheFile ):
		logging.debug( 'touch cache file:'+ cacheFile )
		node = self.cacheFileTable.get( cacheFile, None )
		# assert node
		if not node: 
			logging.warn( 'no cache found:' + cacheFile )
			return False
		node['touched'] = True
		return True

	def buildCacheFilePath( self, srcPath, name = None, **option ):
		#make a name for cachefile { hash of srcPath }	
		category = option.get( 'category', None )
		
		cachePath = self.cachePath
		cacheAbsPath = self.cacheAbsPath

		if category:
			subPath = self.categories.get( category, None )
			if subPath:
				cachePath    += ( '/' + subPath )
				cacheAbsPath += ( '/' + subPath )
			else:
				logging.warning('unkown cache category %s' % repr(category) )

		baseName    = srcPath
		if name: baseName += '@' + name
		mangledName = makeMangledFilePath( baseName )
		
		relPath     = cachePath + '/' + mangledName
		filePath    = cacheAbsPath + '/' + mangledName
		return ( mangledName, relPath, filePath )

	def checkCacheFile( self, srcPath, name = None, **option ):
		mangledName, relPath, filePath = self.buildCacheFilePath( srcPath, name, **option )
		if os.path.exists(filePath):
			return relPath
		else:
			return None

	def getCacheFile( self, srcPath, name = None, **option ):
		mangledName, relPath, filePath = self.buildCacheFilePath( srcPath, name, **option )
		isDir       = option.get( 'is_dir',  False )
		clear       = option.get( 'clear',   False )
		#make an new cache file
		self.cacheFileTable[ relPath ] = {
				'src'     : srcPath,
				'name'    : name,
				'file'    : mangledName,
				'touched' : True,
				'is_dir'  : isDir
			}

		if isDir:
			if os.path.isfile( filePath ):
				os.remove( filePath )
			if not os.path.exists(filePath):
				os.mkdir( filePath )
			elif clear:
				shutil.rmtree( filePath )
				os.mkdir( filePath )
		else:
			#create empty placeholder if not ready
			if os.path.isdir( filePath ):
				shutil.rmtree( filePath )
			if not os.path.exists(filePath):
				fp = open( filePath, 'w' ) 
				fp.close()

		return relPath

	def getCacheDir( self, srcPath, name = None ):
		return self.getCacheFile( srcPath, name, is_dir = True )

	def clearFreeCacheFiles( self ):
		#check if the src file exists, if not , remove the cache file
		logging.info( 'removing free cache file/dir' )
		toRemove = []
		for path, cacheFile in self.cacheFileTable.items():
			if not cacheFile['touched']:
				toRemove.append( path )
				logging.info( 'remove cache file/dir:' + path )
				if cacheFile.get( 'is_dir', False ):
					try:
						shutil.rmtree( path )
					except Exception as e:
						logging.error( 'failed removing cache directory:' + path )
				else:
					try:
						os.remove( path )
					except Exception as e:
						logging.error( 'failed removing cache file:' + path )

		for path in toRemove:
			del self.cacheFileTable[path]

	def getTempDir( self ):
		return TempDir()

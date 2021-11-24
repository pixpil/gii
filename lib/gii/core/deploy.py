import logging
import platform
import sys
import imp
import os
import os.path
import re
import shutil
import hashlib
import time
import pathtools.path

from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from simple_task_queue import task, Task, WorkerPool

from util import FileTool

from . import signals
from . import JSONHelper
from . import tomlHelper

from .guid import generateGUID

from . import project

_GII_DEPLOY_DIR           = 'deploy'
_PACKAGE_CONFIG_NAME      = 'package_config.json'
_PACKAGE_EXTENSION        = '.g'
_PACKAGE_INFO_NAME        = 'packages.json'
_DEPLOY_INFO_NAME         = 'deploy_info.json'

_PACKAGE_FILE_INDEX       = '_fileindex'

@task( 'SavePackage' )
def taskSavePackage( package ):
	package.save()

##----------------------------------------------------------------##
def _fixPath( path ):
		path = path.replace( '\\', '/' ) #for windows
		if path.startswith('./'): path = path[2:]
		return path	

##----------------------------------------------------------------##
def _makePath( base, path ):
	if path:
		return base + '/' + path
	else:
		return base

##----------------------------------------------------------------##
def _affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False

##----------------------------------------------------------------##
def addFolderToZip( zip_file, folder, relativeTo = None, prefix = None ): 
	files = sorted( list( pathtools.path.list_files( folder ) ) )
	packSize = 0
	# print folder
	# print files
	for full_path in files:
		# print 'File added: ' + str(full_path)
		if relativeTo:
			targetpath = os.path.relpath( full_path, relativeTo )
		else:
			targetpath = full_path

		arcname = prefix and prefix + targetpath or targetpath
		arcname = arcname.replace( '\\', '/' )
		zip_file.write( full_path, arcname )
		zfInfo = zip_file.getinfo( arcname )
		csize = zfInfo.compress_size
		packSize += csize

##----------------------------------------------------------------##
def packFolderAsZip ( packPath, compress, folder, relativeTo = None ):
	if compress:
		storage = ZIP_DEFLATED
	else:
		storage = ZIP_STORED

	with ZipFile( packPath, 'w', storage, compresslevel = 9 ) as outputZip:
		addFolderToZip( outputZip, folder, relativeTo )


##----------------------------------------------------------------##
def packFolderAsZap ( packPath, compress, folder, relativeTo = None ):
	import PyZAP
	prefix = None
	builder = PyZAP.ZAPArchiveBuilder()

	files = sorted( list( pathtools.path.list_files( folder ) ) )
	
	if compress:
		compressType = PyZAP.COMPRESS_TYPE_ZSTD
	else:
		compressType = PyZAP.COMPRESS_TYPE_NONE

	for full_path in files:
		# print 'File added: ' + str(full_path)
		if relativeTo:
			targetpath = os.path.relpath( full_path, relativeTo )
		else:
			targetpath = full_path

		arcname = prefix and prefix + targetpath or targetpath
		arcname = arcname.replace( '\\', '/' )
		builder.addFile( full_path, arcname, PyZAP.COMPRESS_TYPE_AUTOMATIC )

	builder.buildFile( packPath, compressType )

##----------------------------------------------------------------##
class DeployConfig( object ):
	def __init__( self, project, name, target ):
		self.project = project
		self.name    = name
		self.target  = target
		self.packageConfigTable = None
		self.meta    = {}
		self.config  = {}

	def init( self ):
		pass

	def getTarget( self ):
		return self.target

	def getName( self ):
		return self.name

	def loadConfig( self, data ):
		self.config = data

	def saveConfig( self ):
		return self.config

	def getConfig( self, key, default = None ):
		return self.config.get( key, default )

	def getMeta( self, id, default = None ):
		return self.meta.get( id, default )

	def setMeta( self, id, value ):
		self.meta[ id ] = value

	def getPackageConfig( self, packageId ):
		#load
		if self.packageConfigTable == None:
			packageConfigName = self.getConfig( 'package_config', _PACKAGE_CONFIG_NAME )
			packageConfigPath = self.project.getDeployConfigPath( packageConfigName )
			self.packageConfigTable = JSONHelper.tryLoadJSON( packageConfigPath ) or {}
		#get
		config = self.packageConfigTable.get( packageId, None )
		if not config:
			config = self.getDefaultPackageConfig()
			self.packageConfigTable[ packageId ] = config
		return config

	def getDefaultPackageConfig( self ):
		return dict(
			mode = 'packed'
		)

	def createContext( self, **option ):
		return DeployContext( self )

	def checkSupported( self ):
		return True

	def preDeploy( self, context ):
		pass
		
	def onDeploy( self, context ):
		pass

	def execute( self, **option ):
		context = self.createContext()
		self.preDeploy( context )
		context.execute()
		self.onDeploy( context )
		return context
	
##----------------------------------------------------------------##
class DeployContextPackageGroup(object):
	def __init__( self, groupId, parentPackage ):
		self.parentPackage = parentPackage
		self.id = groupId
		self.absBasePath = self.parentPackage
		self.files = {}
		self.mappedFiles = {}


##----------------------------------------------------------------##
class DeployContextPackage(object):
	def __init__( self, context, packageId, packageConfig ):
		self.config  = packageConfig
		self.context = context
		self.id = packageId
		self.groups = {}
		self.compressFormat = False
		
		self.files = {}
		self.mappedFiles = {}

		self.deployInfo0 = None
		if context.deployInfo0:
			packageInfo = context.deployInfo0.get( 'packages', None )
			if packageInfo:
				self.deployInfo0 = packageInfo.get( packageId, None )

		#read config
		basePath = self.getConfig( 'base', None )
		if basePath == None:
			self.basePath = packageId
		else:
			self.basePath = basePath
		
		self.absBasePath = context.getAbsPath( self.basePath )

		output = self.getConfig( 'output', None )
		if output:
			self.outputName = output
		else:
			self.outputName = self.id

		forcedMode = context.getParentConfig().getConfig( 'force_package_mode', None )
		forcedCompressMode = context.getParentConfig().getConfig( 'force_compress_mode', None )
		mode = self.getConfig( 'mode', 'packed' )

		if mode == 'root':
			self.mode = mode
			self.compress = False

		elif forcedMode:
			self.mode = forcedMode
			self.compress = False

		else:
			self.mode = mode
			if forcedCompressMode != None:
				self.compress = forcedCompressMode
			else:
				self.compress = self.getConfig( 'compress', True )

		self.compressFormat = self.getConfig( 'compress_format', 'zap' )
		#prepare
		self.prepare()
		self.outputFilePath = None

	def getParentConfig( self ):
		return self.context.getParentConfig()

	def getConfig( self, key, default = None ):
		return self.config.get( key, default )

	def makePath( self, fileName ):
		if self.basePath:
			return self.basePath + '/' + fileName
		else:
			return fileName

	def requestFile( self, name, **option ):
		#TODO:registry
		path = self.makePath( name )
		return path

	def addFile( self, srcPath, **option ):
		outputName = option.get( 'name', None )
		if not outputName:
			outputName = self.context._hashPath( srcPath )
		self.files[ srcPath ] = outputName
		mapped = self.makePath( outputName )
		self.mappedFiles[ srcPath ] = mapped
		self.context.copyFile( srcPath, mapped, **option )
		return mapped

	def getFile( self, srcPath ):
		return self.mappedFiles.get( srcPath, None )

	def hasFile( self, srcPath ):
		if self.mappedFiles.get( srcPath, None ):
			return True
		else:
			return False

	def getBuildPath( self ):
		return self.context.getPath( self.basePath )

	def prepare( self ):
		mode = self.mode
		if mode == 'raw' or mode == 'root':
			_affirmPath( self.context.getPath( self.basePath ) )

		elif mode == 'packed':
			_affirmPath( self.context.getPath( self.basePath ) )

	def save( self ):
		self.outputHash = False
		mode = self.mode
		productPath     = self.context.productPath
		productGamePath = self.context.productGamePath

		if mode == 'root':
			outputBasePath = productPath
		else:
			outputBasePath = productGamePath

		if self.outputName:
			outputPath = outputBasePath + '/' + self.outputName
		else:
			outputPath = outputBasePath
		
		self.srcHash = FileTool.calcDirectoryXXH64( self.absBasePath )
		
		modified = True
		if self.deployInfo0 and self.deployInfo0.get( 'hash_src', None ) == self.srcHash:
			self.outputHash = self.deployInfo0.get( 'hash_pack', None )
			modified = False

		#check file exists?
		if mode == 'raw' or mode == 'root':
			if not os.path.exists( outputPath ):
				modified = True

		elif mode == 'packed':
			packPath = outputPath + _PACKAGE_EXTENSION
			self.outputFilePath = packPath
			if not os.path.exists( packPath ):
				modified = True

		#modified?
		if not modified:
			self.context.notify( 'skip unchanged package:' + self.id )
			return

		#write
		if mode == 'raw' or mode == 'root':
			self.context.notify( 'copy raw package:' + self.id )

			self.context._copyFile( self.absBasePath, outputPath )
			self.outputHash = FileTool.calcDirectoryXXH64( outputPath )

		elif mode == 'packed':
			if not self.outputName:
				raise Exception( 'no deploy output name:' + self.id )

			self.context.notify( 'packing package(%s): %s' % ( self.compressFormat, self.id ) )
			packPath = outputPath + _PACKAGE_EXTENSION
			if os.path.exists( packPath ):
				os.remove( packPath )

			#choose package format
			if self.compressFormat == 'zip':
				packFolderAsZip( packPath, self.compress, self.absBasePath, self.absBasePath )
			else:
				packFolderAsZap( packPath, self.compress, self.absBasePath, self.absBasePath )
			self.outputHash = FileTool.calcFileXXH64( packPath )
			self.outputFilePath = packPath

		else:
			raise Exception( 'invalid output mode:' + repr(mode) )
			

	def saveInfo( self ):
		return {
			'mode'      : self.mode,
			'id'        : self.id,
			'compress'  : self.compress,
			'hash_src'  : self.srcHash,
			'hash_pack' : self.outputHash,
		}

##----------------------------------------------------------------##
class DeployContext(object):
	#TOOLS
	_ignoreFilePattern = [
		'\.git',
		'\.assetmeta',
		'^\..*',
	]

	def _checkFileIgnorable(self, name):
		for pattern in DeployContext._ignoreFilePattern:
			if re.match(pattern, name):
				return True
		return False

	def _hashPath( self, path ):
		name, ext = os.path.splitext( os.path.basename( path ) )
		m = hashlib.md5()
		m.update( path.encode('utf-8') )
		return m.hexdigest()

	def _copyFile( self, src, dst, **option ):
		if not os.path.exists( src ): return False
		if os.path.isdir( src ): #dir
			if not os.path.exists( dst ): os.mkdir( dst )
			if os.path.isdir( dst ):
				for f in os.listdir( src ):
					if self._checkFileIgnorable( f ): continue
					self._copyFile( src + '/' + f, dst + '/' + f, **option )
		else: #file
			needCopy = True
			checkMTime = option.get( 'check_mtime', True )
			if os.path.exists( dst ) and ( checkMTime and os.path.getmtime( src ) <= os.path.getmtime( dst )):
				needCopy = False
			if needCopy:
					try:
						print( 'copy file:{0}->{1}'.format( src, dst ) )
						shutil.copy( src, dst )
					except Exception as e:
						logging.warn( e )
						logging.warn( 'failed copy file:{0}->{1}'.format( src, dst ) )
						return False
		return True

	#main body
	def __init__( self, config ):
		self.config      = config
		self.target      = config.target
		self.project     = config.project

		#Init path
		project = config.project
		target = self.target

		deployBase = project.getPath( _GII_DEPLOY_DIR )
		buildPath = deployBase + '/_build/' + target

		self.buildPath   = buildPath
		self.assetPath   = buildPath + '/asset'
		self.configPath  = buildPath + '/config'
		self.staticPath  = deployBase + '/static/' + target
		self.systemPath  = deployBase + '/system/' + target
		self.systemCommonPath  = deployBase + '/system/common'
		self.staticCommonPath  = deployBase + '/static/common'
		self.productPath = deployBase + '/product/' + target
		self.productGamePath = self.productPath + '/game'

		self.deployInfoPath = buildPath + '/' + _DEPLOY_INFO_NAME

		self.deployInfo = dict(
			packages = {},
			assets   = {},
			session  = generateGUID()
		)

		self.deployInfo0 = JSONHelper.tryLoadJSON( self.deployInfoPath )
		if self.deployInfo0:
			self.deployInfo[ 'assets' ] = self.deployInfo0[ 'assets' ].copy()

		self.assetDeployInfo = self.deployInfo[ 'assets' ]
		#runtime var
		self.assetDeployConfigs = {}

		self.packages    = {}

		self.taskQueue   = []
		self.fileMapping = {}
		self.fileMeta    = {}
		self.assetFileMap = {}
		self.meta        = {}
		self.startTime   = time.time()

	def getProject( self ):
		return self.project

	def getAssetLibrary( self ):
		return self.project.getAssetLibrary()

	def affirmPaths( self ):
		logging.info( 'removing output path: %s' %  self.buildPath )
		# if os.path.isdir( self.buildPath ):
		# 	shutil.rmtree( self.buildPath )
		project = self.project
		deployBase = project.getPath( _GII_DEPLOY_DIR )
		_affirmPath( deployBase )
		_affirmPath( deployBase + '/_build' )
		_affirmPath( deployBase + '/product' )

		_affirmPath( self.buildPath )
		_affirmPath( self.assetPath )
		_affirmPath( self.configPath )

		self.rootPackage    = self.affirmPackage( '__root', 
			dict( mode = 'root',  output = '.' )
		)

		self.staticPackage    = self.affirmPackage( '__root_static', 
			dict( mode = 'root',  output = '.' )
		)

		self.staticPackage    = self.affirmPackage( '__static', 
			dict( mode = 'raw',  output = '.' )
		)

		self.systemPackage    = self.affirmPackage( '_system', 
			dict( mode = 'packed', compress = True )
		)

	def init( self ):
		pass

	def ignorePattern( self ):
		return DeployContext._ignoreFilePattern

	def getParentConfig( self ):
		return self.config

	def getConfig( self, key, default = None ):
		return self.config.getConfig( key, default )

	def getAssetPath( self, path = None ):
		return _makePath( self.assetPath, path )

	def getConfigPath( self, path = None ):
		return _makePath( self.configPath, path )

	def getAbsPath( self, path = None ):
		return self.getPath( path )

	def getPath( self, path = None ):
		return _makePath( self.buildPath, path )

	def setMeta( self, id, var ):
		self.meta[ id ] = var

	def getMeta( self, id, default = None ):
		value = self.meta.get( id, None )
		if value == None:
			return self.config.getMeta( id, default ) 
		else:
			return value

	def getPackage( self, packageId ):
		return self.packages.get( packageId, None )

	def collectAsset( self ):
		assetLibrary = self.getProject().getAssetLibrary()
		return list(assetLibrary.assetTable.values())

	def filterAsset( self, assets ):
		# if self.deployInfo0:
		# 	assetInfo0 = self.deployInfo0.get( 'assets', None )
		# 	if assetInfo0:
		# 		filtered = []
		# 		for asset in assets:
		# 			path = asset.getPath()
		# 			info = assetInfo0.get( path )
		# 			mtime0 = info[ 'mtime' ]
		# 			mtime = asset.getFileTime()
		# 			if mtime0 >= mtime: continue
		# 			filtered.append( asset )
		# 		return filtered
		return assets

	def getAssetDeployMeta( self, assetNode ):
		return None

	def affirmPackage( self, packageId, packageConfig = None ):
		assert packageId
		package = self.packages.get( packageId, None )
		if not package:
			if not packageConfig:
				packageConfig = self.config.getPackageConfig( packageId )
			package = DeployContextPackage( self, packageId, packageConfig )
			self.packages[ packageId ] = package

		return package

	def addConfigFile( self, srcPath, **option ):
		option[ 'package' ] = 'config'
		return self.addFile( srcPath, **option )

	def addFile( self, srcPath, **option ):
		packageId = option.get( 'package', '__root' )
		return self.addFileToPackage( srcPath, packageId, **option )

	def addFileToPackage( self, srcPath , packageId = '__root', **option ):
		package = self.affirmPackage( packageId )
		packedFile = package.addFile( srcPath, **option )
		self.fileMapping[ srcPath ] = packedFile
		return packedFile

	def requestFile( self, filename, **option ):
		packageId = option.get( 'package', '__root' )
		package = self.affirmPackage( packageId )
		return package.requestFile( filename, **option )

	# def getAbsPath( self, path = None):
	def addTask( self, stage, func, *args ):
		task = ( func, args )
		self.taskQueue.append( task )

	def checkFileModified( self, srcPath ):
		absPath = self.getAbsMappedFile( srcPath )
		if not absPath:
			return False
		return int( os.path.getmtime( absPath ) ) >=  int( self.startTime )

	def isNewerFile( self, absPath ):
		return int( os.path.getmtime( absPath ) ) >=  int( self.startTime )

	def copyFile( self, srcPath, dstPath = None, **option ):
		if not dstPath:
			dstPath = os.path.basename( srcPath )
		absDstPath = self.getPath( dstPath )
		self._copyFile( srcPath, absDstPath, **option )

	def copyFilesInDir( self, srcDir, dstDir = None, **option ):
		if not os.path.isdir( srcDir ):
			raise Exception( 'Directory expected' )
		for fname in os.listdir( srcDir ):
			if self._checkFileIgnorable( fname ): continue
			fpath = srcDir + '/' + fname
			self.copyFile( fpath, **option )

	def addFilesFromDir( self, srcDir, **option ):
		if not os.path.isdir( srcDir ):
			raise Exception( 'Directory expected' )
		for fname in os.listdir( srcDir ):
			if self._checkFileIgnorable( fname ): continue
			fpath = srcDir + '/' + fname
			option[ 'name' ] = fname
			self.addFile( fpath, **option )

	def mapFile( self, srcPath, dstPath = None, **option ):
		if not dstPath:
			base = option.get( 'base', 'asset' )
			hashedPath = self._hashPath( srcPath )
			if base:
				dstPath = base + '/' + hashedPath
			else:
				dstPath = hashedPath
		self.fileMapping[ srcPath ] = dstPath
		return dstPath

	def getMappedFile( self, srcPath ):
		return self.fileMapping.get( srcPath, None )

	def getAbsMappedFile( self, srcPath ):
		mapped = self.getMappedFile( srcPath )
		return mapped and self.getPath( mapped ) or None

	def hasFile( self, srcPath ):
		return srcPath in self.fileMapping

	def getFile( self, srcPath ):
		return self.fileMapping.get( srcPath, None )

	def getAbsFile( self, srcPath ):
		return self.getPath( self.getFile( srcPath ) )

	def deployAsset( self, assetNode ):
		mgr = assetNode.getManager()
		if not mgr: return
		mgr.deployAsset( assetNode, self )

	def getAssetDeployInfo( self, assetNode ):
		return self.assetDeployInfo.get( assetNode.getPath(), None )

	def calcAssetDeployConfig( self, assetNode ):
		return assetNode.getDeployConfig()

	def affirmAssetDeployConfig( self, assetNode ):
		config = self.assetDeployConfigs.get( assetNode, None )
		if not config:
			config = self.calcAssetDeployConfig( assetNode )
			self.assetDeployConfigs[ assetNode ] = config
		return config

	def addAssetObjectFile( self, assetNode, key ):
		deployConfig = self.affirmAssetDeployConfig( assetNode )
		policy  = deployConfig.get( 'policy', None )
		packageId = deployConfig.get( 'package', None )
		if packageId == False: return
		if packageId == None: packageId = 'asset'

		objFile = assetNode.getObjectFile( key )
		if objFile:
			packedPath = self.addFileToPackage( objFile, packageId )
			return packedPath
		else:
			logging.warning( 'no object file: %s @ %s', key, assetNode.getPath() )
			return False

	def addAssetObjectFiles( self, assetNode ):
		deployConfig = self.affirmAssetDeployConfig( assetNode )
		policy  = deployConfig.get( 'policy', None )
		packageId = deployConfig.get( 'package', None )
		if packageId == False: return
		if packageId == None: packageId = 'asset'
		packedFiles = {}
		for key, objFile in assetNode.objectFiles.items():
			if not objFile: continue
			packedPath = self.addFileToPackage( objFile, packageId )
			packedFiles[ key ] = packedPath
		return packedFiles

	def replaceInFile( self, srcFile, strFrom, strTo ):
		try:
			fp = open( srcFile, 'rb' )
			data = fp.read()
			fp.close()

			data = data.replace( strFrom.encode('utf-8'), strTo.encode('utf-8') )
			fp = open( srcFile, 'wb' )
			fp.write( data )
			fp.close()
		except Exception as e:
			logging.exception( e )			
		
	def flushTask( self ):
		#TODO: more comprehensive API
		q = self.taskQueue
		self.taskQueue = []
		for t in q:
			func, args = t
			func( *args )

	def save( self ):
		project = self.project
		#write packages
		self.notify( ' >writing into output packages...' )
		_affirmPath( self.productPath )
		_affirmPath( self.productGamePath )
		with WorkerPool():
			for id, package in self.packages.items():
				Task( 'SavePackage' ).promise( package )
				# package.save()

		self.notify( ' >writing package info...' )
		packageInfo = {}

		#meta info
		packageInfo[ 'time' ] = time.strftime('%H:%M:%S %Z %A %Y-%m-%d ')
		packageInfo[ 'timestamp' ] = time.time()
		packageInfo[ 'project_info' ] = project.info
		packageInfo[ 'session' ] = self.deployInfo[ 'session' ]

		packageInfo[ 'packages' ] = packageDatas = {}
		for id, package in self.packages.items():
			if id == '__root': continue
			if id == '__static': continue
			if id == '__root_static': continue
			packageDatas[ id ] = package.saveInfo()

		packageInfoPath = self.productPath + '/' + _PACKAGE_INFO_NAME
		JSONHelper.trySaveJSON( packageInfo, packageInfoPath, 'packge info' )

		self.deployInfo[ 'packages' ] = packageInfo[ 'packages' ]
		self.deployInfo[ 'timestamp' ] = packageInfo[ 'timestamp' ]
		self.deployInfo[ 'time' ] = packageInfo[ 'time' ]
		JSONHelper.trySaveJSON( self.deployInfo, self.deployInfoPath, 'deploy info' )

		self.buildFileIndex()


	def buildFileIndex( self ):
		base = self.productPath
		#build file index for sync usage
		entries = {}
		entries[ 'dirs' ] = dirs = []
		entries[ 'files' ] = files = []

		precalculatedHash = {}
		##fill in precalculated hah
		for id, package in self.packages.items():
			if package.outputFilePath:
				relpath = os.path.relpath( package.outputFilePath, base ).replace( '\\', '/' )
				precalculatedHash[ relpath ] = package.outputHash

		for f in pathtools.path.listdir( base ):
			normalizedPath = os.path.relpath(f, base).replace( '\\', '/' )
			if normalizedPath == _PACKAGE_FILE_INDEX:
				continue

			if os.path.isdir( f ):
				dirs.append( normalizedPath )
			else:
				info = {}
				info[ 'path' ] = normalizedPath
				h =  precalculatedHash.get( normalizedPath, None )
				if h:
					info[ 'hash' ] = h
				else:
					info[ 'hash' ] = FileTool.calcFileXXH64( f )
				info[ 'size' ] = os.path.getsize( f )
				files.append( info )

		JSONHelper.trySaveJSON( entries, base + '/' + _PACKAGE_FILE_INDEX, 'package index' )


	def notify( self, msg ):
		#TODO
		print( msg )


	def execute( self ):
		config = self.config
		project = config.project
		target = self.target

		assetLibrary = project.getAssetLibrary()

		self.notify( ' >Start deploy building...' )
		#execute
		self.affirmPaths()

		logging.info( 'deploy current project' )
		signals.emitNow( 'project.pre_deploy', self )

		#deploy asset library
		self.init()

		self.notify( ' >Collect deployable assets...' )
		#collect deployable assets
		deployable = self.collectAsset()
		filteredDeployable = self.filterAsset( deployable )

		self.notify( ' >Processing asset files...' )


		with WorkerPool():
			for assetNode in filteredDeployable:
				self.deployAsset( assetNode )

		assetInfo = self.deployInfo[ 'assets' ]
		for assetNode in deployable:
			assetInfo[ assetNode.getPath() ] = dict(
					mtime = assetNode.getFileTime(),
				)		
		#callbacks
		self.notify( ' >Processing extra...' )

		with WorkerPool():
			signals.emitNow( 'project.deploy', self )

		assetIndexPath = self.requestFile( 'asset_index', package = 'config' )
		self.setMeta( 'mock_asset_library', assetIndexPath )
		self.notify( ' >Saving asset index...' )
		assetLibrary.saveAssetTable(
				path    = self.getAbsPath( assetIndexPath ), 
				deploy_context  = self,
				mode    = 'deploy'
			)

		#copy static resources
		self.notify( ' >Processing game configurations...' )
		self.addFile( project.getGameConfigPath(), name = 'game', package = 'config'  )

		# self.notify( ' >Processing host resources...' )
		# hostResPath = project.getHostPath( 'resource' )
		# self.addFilesFromDir( hostResPath, package = '__static' )

		self.notify( ' >Processing static files...' )
		if os.path.exists( self.staticCommonPath ):
			self.addFilesFromDir( self.staticCommonPath, package = '__root_static' )

		if os.path.exists( self.staticPath ):
			self.addFilesFromDir( self.staticPath, package = '__root_static', check_mtime = False )

		if os.path.exists( self.systemCommonPath ):
			self.addFilesFromDir( self.systemCommonPath, package = '_system' )

		if os.path.exists( self.systemPath ):
			self.addFilesFromDir( self.systemPath, package = '_system', check_mtime = False )

		#export mock library
		self.notify( ' >Processing game runtime libraries...' )
		
		#finish
		self.notify( ' >Post processing...' )
		self.flushTask()
		signals.emitNow( 'project.post_deploy', self )
		
		#done
		self.notify( ' >Saving...' )
		self.save()

		signals.emitNow( 'project.done_deploy', self )
		self.notify( 'FINISHED.' )

##----------------------------------------------------------------##
_DeployConfigClassRegistry = {}
def registerDeployConfigClass( id, clas ):
	_DeployConfigClassRegistry[ id ] = clas
	clas.classId = id

def getDeployConfigClass( id ):
	return _DeployConfigClassRegistry.get( id, None )

def getDeployConfigClassRegistry( id ):
	return _DeployConfigClassRegistry

registerDeployConfigClass( 'default', DeployConfig )

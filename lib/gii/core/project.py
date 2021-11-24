import logging
import sys
import imp
import os
import os.path
import re
import shutil
import hashlib
import time

from . import signals
from . import JSONHelper
from . import tomlHelper

from .guid import generateGUID
from . import user

##----------------------------------------------------------------##
from .cache   import CacheManager
from .asset   import AssetLibrary
from .deploy  import DeployConfig, DeployContext, getDeployConfigClass
##----------------------------------------------------------------##
_GII_ENV_DIR            = 'env'
_GII_GAME_DIR           = 'game'
_GII_HOST_DIR           = 'host'
_GII_BINARY_DIR         = 'bin'

_GII_PUBLIC_DIR         = 'public'

_GII_ASSET_DIR          = _GII_GAME_DIR + '/asset'
_GII_SCRIPT_LIB_DIR     = _GII_GAME_DIR + '/lib'

_GII_HOST_EXTENSION_DIR = _GII_HOST_DIR  + '/extension'

_GII_ENV_PACKAGE_DIR    = _GII_ENV_DIR  + '/packages'
_GII_ENV_DATA_DIR       = _GII_ENV_DIR  + '/data'
_GII_ENV_LIB_DIR        = _GII_ENV_DIR  + '/lib'
_GII_ENV_CONFIG_DIR     = _GII_ENV_DIR  + '/config'
_GII_ENV_WORKSPACE_DIR  = _GII_ENV_DIR  + '/workspace'
_GII_ENV_CONFIG_MODULES_DIR = _GII_ENV_CONFIG_DIR  + '/modules'
_GII_ENV_CONFIG_DEPLOY_DIR  = _GII_ENV_CONFIG_DIR  + '/deploy'
_GII_ENV_CONFIG_GAME_DIR    = _GII_ENV_CONFIG_DIR  + '/game'

_GII_USER_SETTINGS_FILE    = 'user.settings'
_GII_PROJECT_SETTINGS_FILE = 'project.settings'
_GII_INFO_FILE             = 'project.json'
_GII_CONFIG_FILE           = 'config.json'
_GII_WORKSPACE_CONFIG_FILE = 'workspace.json'


####----------------------------------------------------------------##
_default_config = {
	"excluded_packages" : []
}

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
def _hashPath( path ):
	name, ext = os.path.splitext( os.path.basename( path ) )
	m = hashlib.md5()
	m.update( path.encode('utf-8') )
	return m.hexdigest()

##----------------------------------------------------------------##
class ProjectException(Exception):
	pass

##----------------------------------------------------------------##
class Project(object):
	_singleton=None
	@staticmethod
	def get():		
		return Project._singleton

	@staticmethod
	def findProject( path = None, projectType = None ):
		path = os.path.abspath( path or '' )
		found = False
		while path and not ( path in ( '', '/','\\' ) ):
			#try find normal project
			if   os.path.exists( path + '/' + _GII_ENV_CONFIG_DIR ) \
			and  os.path.exists( path + '/' + _GII_INFO_FILE ) :
				found = True
				break
			#go up level
			opath = path
			path = os.path.dirname( path )
			if path == opath: break

		if found:
			info = JSONHelper.tryLoadJSON( path + '/' + _GII_INFO_FILE )
			return path, info
		else:
			return None, None

	####
	def __init__( self ):
		assert not Project._singleton
		Project._singleton = self
		self.projectType = 'normal'

		self.path      = None
		self.cacheManager = CacheManager()
		self.assetLibrary = AssetLibrary( self )

		self.GUID = None

		self.info = {
			'name'    : 'Name',
			'author'  : 'author',
			'version' : [0,0,1],
			'GUID'    : None
		}

		self.config          = {}
		self.workspaceConfig = {}
		self.userSettings    = {}
		self.projectSettings = {}
		self.moduleConfig    = {}

		self.deployConfigs   = []

	def isCompiledProject( self ):
		return self.mode == 'compiled'

	def getProjectType( self ):
		return self.projectType

	def isLoaded( self ):
		return self.path != None

	def _initPath( self, path ):
		self.path = path

		self.binaryPath           = path + '/' + _GII_BINARY_DIR
		self.gamePath             = path + '/' + _GII_GAME_DIR

		self.envPath              = path + '/' + _GII_ENV_DIR
		self.envPackagePath       = path + '/' + _GII_ENV_PACKAGE_DIR
		self.envDataPath          = path + '/' + _GII_ENV_DATA_DIR
		self.envConfigPath        = path + '/' + _GII_ENV_CONFIG_DIR
		self.envModuleConfigPath  = path + '/' + _GII_ENV_CONFIG_MODULES_DIR
		self.envDeployConfigPath  = path + '/' + _GII_ENV_CONFIG_DEPLOY_DIR
		self.envGameConfigPath    = path + '/' + _GII_ENV_CONFIG_GAME_DIR
		self.envLibPath           = path + '/' + _GII_ENV_LIB_DIR
		self.envWorkspacePath     = path + '/' + _GII_ENV_WORKSPACE_DIR

		self.assetPath            = path + '/' + _GII_ASSET_DIR

		self.scriptLibPath        = path + '/' + _GII_SCRIPT_LIB_DIR

		self.hostPath             = path + '/' + _GII_HOST_DIR
		self.hostExtensionPath    = path + '/' + _GII_HOST_EXTENSION_DIR
		self.publicPath           = path + '/' + _GII_PUBLIC_DIR

	def _affirmPaths( self ):
		#mkdir - lv1
		_affirmPath( self.binaryPath )

		_affirmPath( self.publicPath )

		_affirmPath( self.envPath )
		_affirmPath( self.envPackagePath )
		_affirmPath( self.envDataPath )
		_affirmPath( self.envLibPath )
		_affirmPath( self.envConfigPath )
		_affirmPath( self.envModuleConfigPath )
		_affirmPath( self.envDeployConfigPath )
		_affirmPath( self.envWorkspacePath )
		_affirmPath( self.envWorkspacePath + '/asset' )

		_affirmPath( self.envGameConfigPath )

		_affirmPath( self.gamePath )
		_affirmPath( self.assetPath )
		_affirmPath( self.scriptLibPath )
		
		_affirmPath( self.hostPath )
		_affirmPath( self.hostExtensionPath )
		
	def initEmptyProject( self, path, name ):
		projectPath, info = Project.findProject( path )
		if info:
			raise ProjectException( 'Gii project already initialized:' + info['path'] )
		#
		path = os.path.realpath(path)
		if not os.path.isdir(path):
			raise ProjectException('%s is not a valid path' % path)
		path = path.replace( '\\', '/' )
		self._initPath( path )
		#
		logging.info( 'copy template contents' )
		from .MainModulePath import getMainModulePath
		def ignore( src, names ):
			return ['.DS_Store']
		shutil.copytree( getMainModulePath('template/host'), self.getPath('host'), ignore )
		shutil.copytree( getMainModulePath('template/game'), self.getPath('game'), ignore )
		shutil.copy( getMainModulePath('template/.gitignore'), self.getPath() )
		#
		self._affirmPaths()

		try:
			self.cacheManager.init( _GII_ENV_CONFIG_DIR, self.envConfigPath )
		except OSError as e:
			raise ProjectException('error creating cache folder:%s' % e)

		self.assetLibrary.load( _GII_ASSET_DIR, self.assetPath, self.path, self.envConfigPath )

		signals.emitNow('project.init', self)
		logging.info( 'project initialized: %s' % path )
		self.info['name'] = name
		self.info['GUID'] = generateGUID()
		self.saveConfig()
		self.saveWorkspaceConfig()
		self.saveDeployConfig()
		self.save()
		return True	

	def loadSettings( self, clearFirst = False ):
		if clearFirst:
			self.projectSettings = {}
			self.userSettings = {}
		projectSettingPath = self.getBasePath( _GII_PROJECT_SETTINGS_FILE )
		if os.path.isfile( projectSettingPath ):
			settings = tomlHelper.tryLoadTOML( projectSettingPath )
			if settings:
				self.projectSettings = settings

		userSettingPath = self.getBasePath( _GII_USER_SETTINGS_FILE )
		if os.path.isfile( userSettingPath ):
			settings = tomlHelper.tryLoadTOML( userSettingPath )
			if settings:
				self.userSettings = settings

	def load(self, path):
		path = os.path.realpath(path)
		path = path.replace( '\\', '/' )
		
		self._initPath( path )
		self._affirmPaths()
		os.chdir( path )

		sys.path.insert( 0, self.envLibPath )
		sys.path.insert( 0, self.getBinaryPath( 'python' ) ) #for python extension modules

		self.info            = JSONHelper.tryLoadJSON( self.getBasePath( _GII_INFO_FILE ) )
		self.config          = JSONHelper.tryLoadJSON( self.getConfigPath( _GII_CONFIG_FILE ) )
		self.workspaceConfig = JSONHelper.tryLoadJSON( self.getWorkspacePath( _GII_WORKSPACE_CONFIG_FILE ) )

		self.loadSettings()

		if not self.info:
			self.GUID = generateGUID()
			self.info = {
				'name' : 'name',
				'version' : [0,0,1],
				'GUID' : self.GUID,
			}
			JSONHelper.trySaveJSON( self.info, self.getBasePath( _GII_INFO_FILE ) )
			
		elif not self.info.get( 'GUID', None ):
			self.GUID = generateGUID()
			self.info[ 'GUID' ] = self.GUID
			JSONHelper.trySaveJSON( self.info, self.getBasePath( _GII_INFO_FILE ) )

		if not self.config:
			self.config = {}
			JSONHelper.trySaveJSON( self.config, self.getConfigPath( _GII_CONFIG_FILE ) )

		if not self.workspaceConfig:
			self.workspaceConfig = {}
			JSONHelper.trySaveJSON( self.workspaceConfig, self.getWorkspacePath( _GII_WORKSPACE_CONFIG_FILE ) )

		if not self.userSettings:
			self.userSettings = {}

		if not self.projectSettings:
			self.projectSettings = {}

		if not self.deployConfigs:
			self.deployConfigs = {}
			
		self.cacheManager.load( _GII_ENV_CONFIG_DIR, self.envConfigPath )
		self.assetLibrary.load( _GII_ASSET_DIR, self.assetPath, self.path, self.envConfigPath )

		#will trigger other module
		signals.emitNow( 'project.preload', self )
		signals.emitNow( 'project.load', self )
		
		logging.info( 'project loaded: %s' % path )
		return True

	def loadAssetLibrary( self ):
		#load cache & assetlib
		self.assetLibrary.loadAssetTable()
		self.assetLibrary.loadRemoteFileTable()

	def getGUID( self ):
		return self.GUID

	def getVersion( self ):
		return self.version

	def getVersionString( self ):
		return '%d.%d.%d' % self.getVersion()

	def save( self ):
		logging.info( 'saving current project' )
		signals.emitNow('project.presave', self)
		#save project info & config
		JSONHelper.trySaveJSON( self.info,   self.getBasePath( _GII_INFO_FILE ), 'project info' )

		#save asset & cache
		self.assetLibrary.save()
		self.cacheManager.clearFreeCacheFiles()
		self.cacheManager.save()

		signals.emitNow( 'project.save', self ) #post save
		logging.info( 'project saved' )
		return True

	def saveConfig( self ):
		JSONHelper.trySaveJSON(
			self.config,
			self.getConfigPath( _GII_CONFIG_FILE ),
			'project config'
		)

	def saveModuleConfig( self, moduleId = None ):
		data = self.moduleConfig.get( moduleId, None )
		JSONHelper.trySaveJSON(
			data,
			self.getModuleConfigPath( moduleId + '.cfg.json' ),
			'module config'
		)

	def addDeployConfig( self, name, target, clasId = None, guid = None ):
		print(('deploy config added:', name, target))
		clas = getDeployConfigClass( clasId )
		if not clas:
			raise Exception( 'No deploy config class named:' + clasId )
		config = clas( self, name, target )
		if guid:
			config._GUID = guid
		else:
			config._GUID = generateGUID()
		config.init()
		self.deployConfigs.append( config )
		return config

	def removeDeployConfig( self, config ):
		if not config in self.deployConfigs: return False
		self.deployConfigs.remove( config )
		return True

	def getDeployConfig( self, name ):
		for config in self.deployConfigs:
			if config.name == name:
				return config
		return None

	def getDeployConfigs( self ):
		return self.deployConfigs

	def saveDeployConfig( self ):
		folder = self.getDeployConfigPath()
		for config in self.deployConfigs:
			configData = config.saveConfig()
			data = {
				'class' : type( config ).classId,
				'name'  : config.name,
				'target': config.target,
				'guid'  : config._GUID,
				'config': configData
			}
			JSONHelper.trySaveJSON(
				data,
				self.getDeployConfigPath( id + '.deploy.json' )
			)

	def loadDeployConfig( self ):
		folder = self.getDeployConfigPath()
		if not os.path.exists( folder ):
			logging.warning( 'no deploy config folder' )
			return

		self.deployConfigs = []
		for file in os.listdir( folder ):
			fullPath = os.path.join( folder, file )
			if not ( os.path.isfile( fullPath ) and file.endswith( '.deploy.json' ) ): continue
			data = JSONHelper.tryLoadJSON( fullPath )
			if not data:
				continue

			id = os.path.basename( file )
			clas   = data[ 'class' ]
			name   = data[ 'name' ]
			target = data[ 'target' ]
			guid   = data[ 'guid' ]
			config = self.addDeployConfig( name, target, clas, guid )
			config.loadConfig( data[ 'config' ] )
			config._GUID = guid

	def saveWorkspaceConfig( self ):
		JSONHelper.trySaveJSON( self.workspaceConfig, self.getWorkspacePath( _GII_WORKSPACE_CONFIG_FILE ), 'project workspace config')

	def getRelativePath( self, path ):
		return _fixPath( os.path.relpath( path, self.path ) )

	def getPath( self, path = None ):
		return self.getBasePath( path )

	def getPublicPath( self, path = None ):
		return _makePath( self.publicPath, path )
		
	def getBasePath( self, path=None ):
		return _makePath( self.path, path)

	def getEnvPath( self, path=None ):
		return _makePath( self.envPath, path)

	def getEnvDataPath( self, path=None ):
		return _makePath( self.envDataPath, path)

	def getEnvLibPath( self, path = None ):
		return _makePath( self.envLibPath, path)

	def getHostPath( self, path=None ):
		return _makePath( self.hostPath, path)

	def getPackagePath(self, path=None):
		return _makePath( self.envPackagePath, path)

	def getConfigPath(self, path=None):
		return _makePath( self.envConfigPath, path)

	def getDeployConfigPath(self, path=None):
		return _makePath( self.envDeployConfigPath, path)

	def getModuleConfigPath(self, path=None):
		return _makePath( self.envModuleConfigPath, path)

	def getGameConfigPath(self, path=None):
		return _makePath( self.envGameConfigPath, path)

	def getWorkspacePath(self, path=None):
		return _makePath( self.envWorkspacePath, path)

	def getBinaryPath(self, path=None):
		return _makePath( self.binaryPath, path)

	def getGamePath(self, path=None):
		return _makePath( self.gamePath, path)

	def getAssetPath(self, path=None):
		return _makePath( self.assetPath, path)

	def getScriptLibPath(self, path=None):
		return _makePath( self.scriptLibPath, path)

	def isProjectFile(self, path):
		path    = os.path.abspath( path )
		relpath = os.path.relpath( path, self.path )
		return not (relpath.startswith('..') or relpath.startswith('/'))

	def getConfigDict( self ):
		return self.config

	def getConfig( self, key, default = None ):
		return self.config.get( key, default )

	def setConfig( self, key, value ):
		self.config[ key ] = value
		self.saveConfig()

	def getModuleConfigDict( self, moduleId, affirm = True ):
		config = self.moduleConfig.get( moduleId, None )
		if (not config):
			#try load
			filePath = self.getModuleConfigPath( moduleId + '.cfg.json' )
			if os.path.exists( filePath ):
				config = JSONHelper.tryLoadJSON( filePath )
				if config:
					self.moduleConfig[ moduleId ] = config

			if not config and affirm:
				config = {}
				self.moduleConfig[ moduleId ] = config

		return config

	def getModuleConfig( self, moduleId, key, default = None ):
		configDict = self.getModuleConfigDict( moduleId, False )
		if not configDict: return default
		return configDict.get( key, default )

	def setModuleConfig( self, moduleId, key, value ):
		configDict = self.getModuleConfigDict( moduleId, True )
		configDict[ key ] = value
		self.saveModuleConfig( moduleId )

	def getWorkspaceConfig( self, key, default = None ):
		return self.workspaceConfig.get( key, default )

	def setWorkspaceConfig( self, key, value ):
		self.workspaceConfig[ key ] = value
		self.saveWorkspaceConfig()

	def getUserSetting( self, key, default = None ):
		return self.userSettings.get( key, default )

	def printUserSettings( self ):
		print((self.userSettings))

	def getProjectSetting( self, key, default = None ):
		return self.projectSettings.get( key, default )

	def getSetting( self, key, default ):
		v = self.getUserSetting( key, None )
		if v == None:
			return self.getProjectSetting( key, default )
		else:
			return v

	def getAssetLibrary( self ):
		return self.assetLibrary

	def getCacheManager( self ):
		return self.cacheManager

	def generateID( self ):
		userID = 1
		index = self.globalIndex
		self.globalIndex += 1
		return '%d:%d'%( userID, index )

Project()



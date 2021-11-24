import os
import os.path
import sys
import logging
import platform
import time

import threading

from . import signals
from . import JSONHelper
from . import tomlHelper

from . import globalSignals
from .EditorTimer    import EditorTimer
from .EditorModule   import EditorModule, EditorModuleManager
from .project        import Project
from .package        import PackageManager
from .MainModulePath import getMainModulePath
from .Command        import EditorCommandRegistry
from .RemoteCommand  import RemoteCommandRegistry, RemoteCommand

from .InstanceHelper import checkSingleInstance, setRemoteArgumentCallback, sendRemoteMsg

from .URLHandler import encodeGiiURL

from . import AssetUtils

_GII_PACKAGES_FOLDER = 'packages'
_GII_APP_CONFIG_FILE = 'config.json'
_GII_APP_USER_SETTINGS_FILE = 'user.settings'

sys.setrecursionlimit(2000)

class EditorApp(object):
	_singleton = None

	@staticmethod
	def get():
		return _singleton

	def __init__(self):
		assert(not EditorApp._singleton)
		EditorApp._singleton = self
		EditorModuleManager.get()._app = self

		self.defaultMainloopBudget = 0.005

		self.initialized   = False
		self.projectLoaded = False
		self.flagModified  = False
		self.debugging     = False
		self.running       = False

		self.basePath      = os.environ[ 'GII_BASE_PATH' ] or getMainModulePath()
		self.basePath = self.basePath.replace('\\','/')
		
		self.userPath      = False
		self.dataPaths     = []
		self.config        = {}
		self.settings      = {}
		self.packageManager   = PackageManager()

		self.timers = []

		self.commandRegistry       = EditorCommandRegistry.get()
		self.remoteCommandRegistry = RemoteCommandRegistry.get()
		
		self.registerDataPath( self.getPath('data') )

		signals.connect( 'module.register', self.onModuleRegister )
		self.setupUserEnvironment()

		self.loadConfig()
		self.loadUserSettings()
		

	def onModuleRegister(self, m):		
		if self.running:
			logging.info('registered in runtime:'+m.getName())
			EditorModuleManager.get().loadModule(m)

	def setupUserEnvironment( self ):
		#affirm user path
		homePath = os.path.expanduser("~")
		userPath = homePath + '/.gii'
		if os.path.isdir( userPath ):
			self.userPath = userPath
		else:
			self.userPath = False

	def init( self, **options ):
		if options.get( 'stop_other_instance', False ):
			if not checkSingleInstance():
				retryCount = 5
				logging.warning( 'running instance detected, trying to shut it down' )
				sendRemoteMsg( 'shut_down' )
				ready = False
				for i in range( retryCount ):
					time.sleep( 2 )
					if checkSingleInstance():
						ready = True
						break
				if not ready:
					logging.warning( 'timeout for shuting down other instance' )
					return False

		else:
			if not checkSingleInstance():
				logging.warning( 'running instance detected' )
				return False

		if self.initialized: return True

		
		if not options.get( 'load_compiled_project', False ):
			self.openProject( projectType = 'normal' )
		else:
			self.openProject( projectType = 'compiled' )
		
		#scan packages
		excludePackages = self.getProject().getConfig( 'excluded_packages' )
		self.packageManager.addExcludedPackage( excludePackages )

		#scan builtin packages
		logging.info( 'scanning builtin packages' )
		if not self.packageManager.scanPackages( self.getPath( _GII_PACKAGES_FOLDER ) ):
			return False

		#scan user packages
		logging.info( 'scanning user packages' )
		if self.userPath:
			if os.path.isdir( self.getUserPath( _GII_PACKAGES_FOLDER ) ):
				self.packageManager.scanPackages( self.getUserPath( _GII_PACKAGES_FOLDER ) )

		#scan project packages
		logging.info( 'scanning project packages' )
		if self.getProject().isLoaded():
			self.packageManager.scanPackages( self.getProject().envPackagePath )

		#modules
		EditorModuleManager.get().loadAllModules()

		signals.emitNow( 'module.loaded' ) #some pre app-ready activities
		signals.dispatchAll()

		self.getProject().loadAssetLibrary()
		self.getProject().loadDeployConfig()

		self.initialized = True
		self.running     = True

		signals.connect( 'app.remote', self.onRemote )

		return True


	def run( self, **kwargs ):
		if not self.initialized: 
			if not self.init( **kwargs ):
				return False
		hasError = False
		self.resetMainLoopBudget()
		
		try:
			signals.emitNow('app.pre_start')

			self.getProject().getAssetLibrary().scanProject( full = True )
			signals.emitNow('app.asset_scanned')
			EditorModuleManager.get().startAllModules()

			signals.emitNow('app.start')
			signals.dispatchAll()

			self.saveConfig()

			logging.info( 'app ready' )
			EditorModuleManager.get().tellAllModulesAppReady()
			signals.emit('app.ready')

			self.lastTimerPoint = 0
			logging.info( 'enter main loop' )
			#main loop
			while self.running:
				self.doMainLoop()

		except Exception as e:
			#TODO: popup a alert window?
			logging.exception( e )
			hasError = True

		signals.emitNow('app.close')

		signals.dispatchAll()
		EditorModuleManager.get().stopAllModules()
		
		if not hasError:
			#save project
			self.getProject().save()

		signals.dispatchAll()
		EditorModuleManager.get().unloadAllModules()
		return True

	def setMainLoopBudget( self, budget = 0.001 ):
		self.mainLoopBudget = budget

	def resetMainLoopBudget( self ):
		return self.setMainLoopBudget( self.defaultMainloopBudget )

	def setMinimalMainLoopBudget( self ):
		return self.setMainLoopBudget( 0.001 )

	# def doMainLoop( self ):
	# 	budget = 0.010
	# 	t0 = time.time()
	# 	EditorModuleManager.get().updateAllModules()
	# 	signals.dispatchAll()
	# 	signals.emitNow( 'app.update' )
	# 	t1 = time.time()
	# 	elapsed = t1 - t0
	# 	rest = budget - elapsed
	# 	if rest > 0.001:
	# 		time.sleep( rest )

	def doMainLoop( self ):
		t0 = time.perf_counter()
		budget = self.mainLoopBudget
		EditorModuleManager.get().updateAllModules()
		signals.emitNow( 'app.update' )

		self.updateTimers()
		signals.dispatchAll()

		t1 = time.perf_counter()
		elapsed = t1 - t0
		rest = budget - elapsed

		if rest > 0.001:
			time.sleep( rest )

	def tryStop( self, timeout = 0 ):
		if EditorModuleManager.get().confirmStopModules():
			self.stop()
			return True
		else:
			return False

	def stop( self ):
		self.running = False
		self.saveConfig()
	
	#timer
	def callLater( self, waitTime, func ):
		timer = self.addTimer()
		timer.setCallback( func )
		timer.setSingleShot( True )
		timer.setDestroyOnStop( True )
		timer.setInterval( waitTime )
		timer.start()
		return timer

	def addTimer( self, **kwargs ):
		timer = EditorTimer( **kwargs )
		self.timers.append( timer )
		return timer

	def updateTimers( self ):
		t1 = time.perf_counter() * 1000.0 #msecs for unit
		dt = t1 - self.lastTimerPoint
		if dt < 1: return
		self.lastTimerPoint = t1
		timers = self.timers
		deadTimers = []
		for timer in timers:
			if timer.destroyed:
				deadTimers.append( timer )
			else:
				timer.update( dt )
		if deadTimers:
			for dead in deadTimers:
				timers.remove( dead )

	#config
	def getUserSetting( self, key, default = None ):
		prj = Project.get()
		if prj:
			v = prj.getSetting( key, None )
			if v != None: return v
		return self.settings.get( key, default )

	def printUserSettings( self ):
		print((self.settings))

	def loadUserSettings( self ):
		path = self.getUserPath( _GII_APP_USER_SETTINGS_FILE )
		if os.path.isfile( path ):
			loaded = tomlHelper.tryLoadTOML( path )
		else:
			loaded = False
		if loaded:
			self.settings = loaded
		else:
			self.settings = {}

	def saveConfig( self ):
		JSONHelper.trySaveJSON(
			self.config,
			self.getUserPath( _GII_APP_CONFIG_FILE ), 'application config'
		)

	def loadConfig( self ):
		loaded = JSONHelper.tryLoadJSON( self.getUserPath( _GII_APP_CONFIG_FILE ) )
		if loaded:
			config = self.config
			for k, v in loaded.items():
				config[ k ] = v
		else:
			self.saveConfig()

	def setConfig( self, name, value, saveNow = True ):
		self.config[name] = value
		if saveNow:
			self.saveConfig()

	def getConfig( self, name, default = None ):
		return self.config.get( name, default )

	def affirmConfig( self, name, default = None ):
		value = self.config.get( name, None )
		if value == None:
			self.config[ name ] = default
			return default

	def getModule(self, name):
		return EditorModuleManager.get().getModule( name )

	def affirmModule(self, name):
		return EditorModuleManager.get().affirmModule( name )

	def createCommandStack( self, stackName ):
		return self.commandRegistry.createCommandStack( stackName )

	def getCommandStack( self, stackName ):
		return self.commandRegistry.getCommandStack( stackName )

	def clearCommandStack( self, stackName ):
		stack = self.commandRegistry.getCommandStack( stackName )
		if stack:
			stack.clear()

	def doCommand( self, fullname, *args, **kwargs ):
		return self.commandRegistry.doCommand( fullname, *args, **kwargs )

	def undoCommand( self, popOnly = False ):
		return self.commandRegistry.undoCommand( popOnly )

	def makeURL( self, base, **data ):
		return encodeGiiURL( base, data )

	def getCommonSupportPath( self, path = None ):
		base = 'support/common'
		if path:
			return self.getPath( base + '/' + path )
		else:
			return self.getPath( base )

	def getNativeSupportPath( self, path = None ):
		base = 'support/' + self.getPlatformName()
		if path:
			return self.getPath( base + '/' + path )
		else:
			return self.getPath( base )

	def getPath( self, path = None ):
		if path:
			return self.basePath + '/' + path
		else:
			return self.basePath

	def getUserPath( self, path = None ):
		userPath = self.userPath or self.basePath
		if path:
			return userPath + '/' + path
		else:
			return userPath

	def getPythonPath( self ):
		return sys.executable

	def findDataFile( self, fileName ):
		for path in self.dataPaths:
			f = path + '/' + fileName
			if os.path.exists( f ):
				return f
		return None

	def registerDataPath( self, dataPath ):
		self.dataPaths.append( dataPath )

	def getProject( self ):
		return Project.get()

	def isCompiledProject( self ):
		return Project.get().isCompiledProject()

	def openProject( self, basePath = None, projectType = 'normal' ):
		if self.projectLoaded: return Project.get()
		projectPath, projectInfo = Project.findProject( basePath, projectType )
		if not projectPath:
			raise Exception( 'no valid gii project found' )
		proj = Project.get()
		proj.load( projectPath )
		self.projectLoaded = True
		self.registerDataPath( proj.getEnvPath('data') )
		return proj

	def getAssetLibrary( self ):
		return self.getProject().getAssetLibrary()
	
	def isDebugging( self ):
		return False

	def showFileInOS( self, url ):
		AssetUtils.showFileInBrowser( url )

	def openFileInOS( self, url ):
		AssetUtils.openFileInOS( url )

	def getPlatformName( self ):
		name = platform.system()
		if name == 'Linux':
			return 'linux'
		elif name == 'Darwin':
			return 'osx'
		elif name == 'Windows':
			return 'windows'
		else:
			raise Exception( 'what platform?' + name )

	def onRemote( self, data, output, eventFinish ):
		self.remoteCommandRegistry.doCommand( data, output )
		eventFinish.set()

app = EditorApp()

##----------------------------------------------------------------##
def _onRemoteArgument( data, output ):
		#warning: comes from another thread
		eventFinish = threading.Event()
		signals.emit( 'app.remote', data, output, eventFinish )
		eventFinish.wait( 1.0 )
		if not eventFinish.isSet():
			logging.warning( 'remote command failed:' + repr(data) )

setRemoteArgumentCallback( _onRemoteArgument )


##----------------------------------------------------------------##
class RemoteCommandShutDown( RemoteCommand ):
	name = 'shut_down'
	def run( self, *args ):
		app.stop()
		


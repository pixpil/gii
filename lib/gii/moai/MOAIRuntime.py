import logging
import os.path
from gii.core import signals, EditorModule, RemoteCommand, app, printTraceBack
import base64

# from gii.core import Module, signals, getAppPath, unregisterModule, registerModule, App, Project

from AKU import getAKU, _LuaTable, _LuaThread, _LuaObject, _LuaFunction

from .exceptions import *
from .MOAIInputDevice import MOAIInputDevice
from .LuaTableProxy   import LuaTableProxy

##----------------------------------------------------------------##
_G   = LuaTableProxy( None )
_GII = LuaTableProxy( None )

signals.register( 'lua.msg' )
signals.register( 'moai.clean' )
signals.register( 'moai.reset' )
signals.register( 'moai.ready' )

##----------------------------------------------------------------##
from . import bridge

##----------------------------------------------------------------##
## MOAIRuntime
##----------------------------------------------------------------##
class MOAIRuntime( EditorModule ):
	_singleton=None

	@staticmethod
	def get():
		return MOAIRuntime._singleton

	def __init__(self):
		assert not MOAIRuntime._singleton
		MOAIRuntime._singleton = self
		super(MOAIRuntime, self).__init__()		

		self.paused            = False
		self.GLContextReady    = False
		
		self.luaModules        = []
		self.luaDelegates      = {}

		self.inputDevices      = {}
		self.lastInputDeviceId = 0

	def getName(self):
		return 'moai'

	def getDependency(self):
		return []	

	##----------------------------------------------------------------##
	def getLuaEnv( self ):
		return _G

	def getRuntimeEnv( self ):
		return _GII

	#-------Context Control
	def initContext(self):
		global _G
		global _GII

		self.luaModules        = []

		self.inputDevices      = {}
		self.lastInputDeviceId = 0
		
		aku = getAKU()
		self.GLContextReady = False

		logging.info('init AKU...')
		aku.resetContext()
		aku.setInputConfigurationName( b'GII' )
		logging.info('init Lua runtime...')

		#inject python env
		lua = aku.getLuaRuntime()
		_G._setTarget( lua.globals() )
		_G['GII_PYTHON_BRIDGE']            = bridge
		_G['GII_DATA_PATH']                = self.getApp().getPath('data')

		_G['GII_LIB_LUA_PATH']              = self.getApp().getPath('lib/lua')
		_G['GII_PROJECT_ENV_LUA_PATH']     = self.getProject().getEnvLibPath( 'lua' )
		_G['GII_PROJECT_ASSET_PATH']       = self.getProject().getAssetPath()
		_G['GII_PROJECT_SCRIPT_LIB_PATH']  = self.getProject().getScriptLibPath()
		#TODO
		_G['GII_VERSION_MAJOR']            = 0
		_G['GII_VERSION_MINOR']            = 1
		_G['GII_VERSION_REV']              = 0

		logging.info( 'loading gii lua runtime' )
		# aku.runScript(
		# 	self.getApp().getPath( 'lib/lua/MOAIInterfaces.lua' )
		# 	)

		aku.runScript(
			self.getApp().getPath( 'lib/lua/init.lua' )
			)


		_GII._setTarget( _G['gii'] )

		assert _GII, "Failed loading Gii Lua Runtime!"
		#finish loading lua bridge
		
		self.AKUReady      = True
		self.RunningScript = False
		self.paused        = False
		self.GLContextInitializer = None
		
		# getAKU().setFuncOpenWindow( self.onOpenWindow )		

	def initGLContext( self ):
		if self.GLContextReady: return True
		logging.info('init GL context')
		from gii.qt.controls.GLWidget import GLWidget
		#initialize MOAI with main Context
		assert( GLWidget.getMainContext().isValid() )
		
		# GLWidget.getSharedWidget().makeCurrent()
		GLWidget.makeMainContextCurrent()

		getAKU().detectGfxContext()

		self.GLContextReady = True
		return True

	def onStart( self ):
		pass

	def needUpdate( self ):
		return True

	def onUpdate( self ):
		if not self.AKUReady: return
		getAKU().updateSupport()
		self.stepGC( 50 )

	def onAssetImported( self ):
		self.updateAKU()
		self.updateNodeMgr()
		self.onUpdate()

	def reset(self):
		if not self.AKUReady: return
		self.cleanLuaReferences()
		self.initContext()
		self.setWorkingDirectory( self.getProject().getPath() )
		signals.emitNow( 'moai.reset' )
		signals.emitNow( 'moai.ready' )

	def onOpenWindow( self, title, w, h ):
		raise Exception( 'No GL context provided.' )

	#------Manual Control For MOAI Module
	#TODO: move function below into bridge module
	def updateNodeMgr(self):
		_GII.updateNodeMgr()

	def stepGC(self, step = 0):
		# print( 'step gc', step )
		_GII.stepGC(step)
		
	def stepSim(self, step):
		_GII.stepSim(step)
		
	def setBufferSize(self, w,h):
	#for setting edit canvas size (without sending resize event)
		_GII.setBufferSize(w,h) 

	def changeRenderContext(self, contextId, w, h ):
		_GII.changeRenderContext( contextId or False, w or False, h or False )

	def createRenderContext( self, key, clearColor = (0,0,0,0) ):
		_GII.createRenderContext( key, *clearColor )

	#### Delegate Related
	def loadLuaDelegate( self, scriptPath , owner = None, **option ):
		if not option.get('forceReload', False): #find in cache first
			delegate = self.luaDelegates.get( scriptPath )
			if delegate: return delegate
		delegate = MOAILuaDelegate( owner )
		delegate.load( scriptPath )
		self.luaDelegates[ scriptPath ] = delegate
		return delegate

	def loadLuaWithEnv( self, file, env = None, **option ):
		try:
			if env:
				assert isinstance( env, dict )
			return _GII.loadLuaWithEnv( file, env, option.get( 'isdelegate', False ) )
		except Exception as e:
			logging.error( 'error loading lua:\n' + str(e) )

	####  LuaModule Related
	def registerLuaModule(self, m):
		self.luaModules.append(m)
		registerModule(m)
	
	#clean holded lua object(this is CRITICAL!!!)
	def cleanLuaReferences(self):
		logging.info('clean lua reference')
		#clear lua module
		for m in self.luaModules:
			unregisterModule(m)

		bridge.clearSignalConnections()
		bridge.clearLuaRegisteredSignals()
		#clear lua object inside introspector
		introspector=self.getModule('introspector')
		if introspector:
			instances = introspector.getInstances()
			for ins in instances:
				if isinstance(ins.target,(_LuaTable, _LuaObject, _LuaThread, _LuaFunction)):
					ins.clear()

		signals.emitNow('moai.clean')

	#General Control
	def setWorkingDirectory(self, path):
		logging.info('change moai working path:' + path )
		getAKU().setWorkingDirectory(path)

	def pause(self, paused=True):
		self.paused=paused
		getAKU().pause(self.paused)

	def resume(self):
		self.pause(False)
	
	def execConsole(self,command):
		self.runString(command)
		
	def updateAKU(self):
		if not self.AKUReady: return False
		if self.paused: return False	
		try:
			getAKU().update()
		except MOAIException as e:
			self.handleException(e)
			return False
		return True

	def renderAKU(self):
		if not self.AKUReady: return False
		try:
			getAKU().render()
		except MOAIException as e:
			self.handleException(e)
			return False
		return True

	def evalScript(self, src):
		self.RunningScript = src
		if not src: return
		try:
			_GII.evalScript( src )
		except MOAIException as e:
			self.handleException(e)
			return False
		return True

	def runScript(self,src):		
		self.RunningScript = src
		if not src: return
		try:
			getAKU().runScript(src)
		except MOAIException as e:
			self.handleException(e)
			return False
		return True

	def runString(self,string):		
		try:
			getAKU().runString(string)
		except MOAIException as e:
			self.handleException(e)
			return False
		return True

	def requireModule( self, modulename ):
		return self.runString( 'require "%s"' % modulename )

	def handleException(self,e):
		code = e.code
		if code=='TERMINATE':
			self.AKUReady      = False
			self.RunningScript = False
		else:
			logging.error( 'error loading lua:\n' + str(e) )

	#Input Device Management
	def getInputDevice(self, name):
		return self.inputDevices.get(name,None)

	def addInputDevice(self, name):
		device = MOAIInputDevice(name, self.lastInputDeviceId)
		self.inputDevices[name] = device
		self.lastInputDeviceId += 1

		getAKU().reserveInputDevices(self.lastInputDeviceId)
		for inputDevice in list(self.inputDevices.values()):
			inputDevice.onRegister()
		return device

	def addDefaultInputDevice( self, name='device' ):
		logging.info( 'add input device: ' + str( name ) )
		device = self.addInputDevice(name)
		device.addSensor('touch',       'touch')
		device.addSensor('pointer',     'pointer')
		device.addSensor('keyboard',    'keyboard')
		device.addSensor('mouseLeft',   'button')
		device.addSensor('mouseRight',  'button')
		device.addSensor('mouseMiddle', 'button')
		device.addSensor('level',       'level')
		device.addSensor('compass',     'compass')
		for i in range( 0, 4 ):
			device.addJoystickSensors( i + 1 )
		return device

	#----------
	def onLoad(self):
		self.AKUReady = False
		signals.tryConnect ( 'console.exec', self.execConsole )
		
		#send asset sync signals
		signals.connect( 'asset.imported_all', self.onAssetImported )

		self.initContext()
		self.setWorkingDirectory( self.getProject().getPath() )
		self.initGLContext()
		# scriptInit = self.getProject().getScriptPath( 'init.lua' )
		# if os.path.exists( scriptInit ):
		# 	getAKU().runScript( scriptInit )

	def onUnload(self):
		# self.cleanLuaReferences()
		self.AKUReady   = False
		pass



##----------------------------------------------------------------##
## Delegate
##----------------------------------------------------------------##
class MOAILuaDelegate(object):
	def __init__(self, owner=None, **option):
		self.scriptPath   = None
		self.scriptEnv    = None
		self.owner        = owner
		self.name         = option.get( 'name', None )

		self.extraSymbols = {}
		self.clearLua()
		signals.connect('moai.clean', self.clearLua)
		if option.get( 'autoReload', True ):
			signals.connect('moai.reset', self.reload)

	def load( self, scriptPath, scriptEnv = None ):
		self.scriptPath = scriptPath
		self.scriptEnv  = scriptEnv
		runtime = MOAIRuntime.get()
		try:
			env = {
				'_owner'      : self.owner,
				'_delegate'   : self
			}
			if self.scriptEnv:
				env.update( self.scriptEnv )
			if self.name:
				env['_NAME'] = env.name
			self.luaEnv = runtime.loadLuaWithEnv( scriptPath, env, isdelegate = True )
			return True
			
		except Exception as e:
			logging.exception( e )
			return False

	def reload(self):
		if self.scriptPath: 
			self.load( self.scriptPath, self.scriptEnv )
			for k,v in list(self.extraSymbols.items()):
				self.setEnv(k,v)

	def setEnv(self, name ,value, autoReload = True):
		if autoReload : self.extraSymbols[name] = value
		self.luaEnv[name] = value

	def getEnv(self, name, defaultValue = None):
		v = self.luaEnv[name]
		if v is None : return defaultValue
		return v

	def safeCall(self, method, *args):
		if not self.luaEnv:
			printTraceBack()
			logging.error( 'trying call a empty lua delegate, owned by %s' % repr( self.owner ) )
			return
		m = self.luaEnv[method]
		if not m: return
		try:
			return m(*args)
		except Exception as e:
			# logging.exception( e )
			print(e)
	
	def safeCallMethod( self, objId, methodName, *args ):
		if not self.luaEnv: 
			printTraceBack()
			logging.error( 'trying call a empty lua delegate, owned by %s' % repr( self.owner ) )
			return
		obj = self.luaEnv[objId]
		if not obj: return
		method = obj[methodName]
		if not method:
			logging.error( 'method not found:%s, owned by %s' % ( methodName, repr( self.owner ) ) )
			return
		try:
			return method( obj, *args )
		except Exception as e:
			# logging.exception( e )
			print(e)

	def call(self, method, *args):
		m = self.luaEnv[method]
		return m(*args)

	def callMethod( self, objId, methodName, *args ):
		obj = self.luaEnv[objId]
		method = obj[methodName]
		return method( obj, *args )

	def clearLua(self):
		self.luaEnv=None


MOAIRuntime().register()


##----------------------------------------------------------------##
def getLuaRuntime():
	return getAKU().getLuaRuntime()

def createLuaTable( *args, **kwargs ):
	return getLuaRuntime().table( *args, **kwargs )

def createLuaTableFrom( *args ):
	return getLuaRuntime().table_from( *args )

def decodeStr( data ):
	s = str( base64.b64decode( data ), 'utf-8' )
	return s

##----------------------------------------------------------------##
class RemoteCommandEvalScript( RemoteCommand ):
	name = 'eval'
	def run( self, *args ):
		if len( args ) >= 1:
			# s = ' '.join( args )
			src = decodeStr( args[0] )
			runtime = app.getModule( 'moai' )
			print('>-----------------')
			print('> eval script ->')
			runtime.evalScript( src )
			print('------------------')

##----------------------------------------------------------------##
class RemoteCommandEvalScript( RemoteCommand ):
	name = 'eval_remote'
	def run( self, *args ):
		if len( args ) >= 1:
			# s = ' '.join( args )
			src = decodeStr( args[0] )
			signals.emit( 'console.exec_remote', src )


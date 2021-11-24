import os
import os.path
import logging
import json
import dirsync

# from util import FileTool

from gii.core              import *
from gii.moai.MOAIRuntime \
	import \
	MOAIRuntime, MOAILuaDelegate, LuaTableProxy, _G, _LuaTable, _LuaObject


signals.register ( 'mock.init' )
##----------------------------------------------------------------##
_MOCK = LuaTableProxy( None )
_MOCK_EDIT = LuaTableProxy( None )

_MOCK_GAME_CONFIG_NAME = 'game_config.json'

def isMockInstance( obj, name ):
	if isinstance( obj, _LuaObject ):
		return  _MOCK.isInstance( obj, name )
	else:
		return False

def getMockClassName( obj ):
	if isinstance( obj, _LuaTable ):
		clas = obj.__class
		if clas: return clas.__name
	return None

def loadMockAsset( path ):
	result = _MOCK.loadAsset( path )
	if not result: return None
	return result[ 0 ]

def getGameModule( name ):
	return _G.getGameModule( name )

def findMockClass( name ):
	return _G.findClass( name )
	
##----------------------------------------------------------------##
class MockRuntime( EditorModule ):
	
	def getDependency(self):
		return [ 'moai', 'game_preview', 'script_library' ]

	def getName(self):
		return 'mock'

	def onLoad(self):
		self.affirmConfigFile()
		self.runtime  = self.getManager().affirmModule( 'moai' )

		self.setupLuaModule()		

		signals.connect( 'project.load', self.onProjectLoaded )
		signals.connect( 'moai.reset', self.onMoaiReset )
		signals.connect( 'moai.ready', self.onMoaiReady )

		signals.connect( 'app.asset_scanned', self.postAssetScan )
		signals.connect( 'project.post_deploy', self.postDeploy )
		signals.connect( 'project.presave',     self.preProjectSave )

		self.initMock()

		self.syncBuiltinAsset()

	def affirmConfigFile( self ):
		proj = self.getProject()
		self.configPath = proj.getConfigPath( _MOCK_GAME_CONFIG_NAME )
		asetIndexPath = proj.getRelativePath( self.getAssetLibrary().assetIndexOutputPath )

		if os.path.exists( self.configPath ):
			data = JSONHelper.loadJSON( self.configPath )
			#fix invalid field
			if data.get( 'asset_library', None ) != asetIndexPath: #fix assetlibrary path
				data['asset_library'] = asetIndexPath
				JSONHelper.trySaveJSON( data, self.configPath)
			return
		#create default config
		defaultConfigData = {
			"asset_library": asetIndexPath ,
			"texture_library": "env/config/texture_library.json",
			"layers" : [
				{ "name" : "default",
					"sort" : "priority_ascending",
					"clear": False
				 },
			]
		}
		JSONHelper.trySaveJSON( defaultConfigData, self.configPath )


	def postAssetScan( self ):
		self.postInitMock()
		# self.getModule( 'game_preview' ).updateView()

	def postDeploy( self, context ):
		configDeployPath = context.requestFile( 'game_config', package = 'config' )
		context.setMeta( 'game_config', configDeployPath )
		game = _MOCK.game
		data = json.loads( game.saveConfigToString( game ) )
		data[ 'asset_library' ]   = context.getMeta( 'mock_asset_library',   False )
		data[ 'texture_library' ] = context.getMeta( 'mock_texture_library', False )
		data[ 'script_library'  ] = context.getMeta( 'mock_script_library',  False )
		JSONHelper.trySaveJSON( data, context.getAbsPath( configDeployPath ), 'deploy game info' )

	def setupLuaModule( self ):
		from gii.qt.controls.GLWidget import GLWidget
		# GLWidget.getSharedWidget().makeCurrent()
		GLWidget.makeMainContextCurrent()
		
		project = self.getProject()
		self.runtime.requireModule( 'mock_edit' )
		_MOCK._setTarget( _G['mock'] )
		_MOCK_EDIT._setTarget( _G['mock_edit'] )
		_MOCK.setDeveloperMode()
		_MOCK.setupEnvironment( 
			project.getPath(),
			project.getGameConfigPath()
		)

	def syncAssetLibrary(self): #TODO:
		pass

	def syncBuiltinAsset( self ):
		project = self.getProject()
		assetRootPath = project.getAssetPath( '__mock' )
		srcPath = project.getScriptLibPath( 'mock/builtin_asset' )
		if os.path.exists( srcPath ):
			dirsync.sync( str(srcPath), str(assetRootPath), 'sync', purge = True, verbose = True, create = True )

	def initMock( self ):
		logging.info( 'init mock runtime' )
		try:
			_MOCK.init( self.configPath, True )
		except Exception as e:
			raise e

	def postInitMock( self ):
		logging.info( 'init mock common data' )
		try:
			game = _MOCK.game
			game.initCommonDataFromEditor( game )
			w, h = game.getTargetDeviceResolution( game )
			preview = self.getModule( 'game_preview' )
			if preview:
				preview.setTargetScreenSize( w, h )
			signals.emit( 'mock.init' )
			proj = self.getProject()
			_MOCK.addEntityIconFolder( app.getPath( 'data/gizmo' ) )
			_MOCK.addEntityIconFolder( app.getUserPath( 'data/gizmo' ) )
			_MOCK.addEntityIconFolder( proj.getEnvDataPath( 'gizmo' ) )
		except Exception as e:
			raise e


	def onProjectLoaded(self,prj):
		self.syncAssetLibrary()

	def preProjectSave( self, prj ):
		game = _MOCK.game
		game.saveConfigToFile( game, self.configPath )

	def onMoaiReset(self):		
		self.setupLuaModule()

	def onMoaiReady( self ):
		self.initMock()

	def getMockEnv( self ):
		return _MOCK

	def getMockEditEnv( self ):
		return _MOCK_EDIT

	def getLuaEnv( self ):
		return _G

	def getComponentTypeList( self ):
		pass

	def getEntityTypeList( self ):
		pass


##----------------------------------------------------------------##	
MockRuntime().register()


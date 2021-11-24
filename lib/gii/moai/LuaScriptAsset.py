import os
import os.path
import subprocess
import hashlib

from simple_task_queue import task, Task, WorkerPool

from .MOAIRuntime import *
from .MOAIRuntime import _G, _GII
from gii.core import *

from .ScriptHelpers import compileLua

##--------------------------------------------##
signals.register ( 'script.load'   )
signals.register ( 'script.reload' )
signals.register ( 'script.unload' )

##----------------------------------------------------------------##
def getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
def _hashPath( path ):
	name, ext = os.path.splitext( os.path.basename( path ) )
	m = hashlib.md5()
	m.update( path.encode('utf-8') )
	return m.hexdigest()

def _affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False

def _convertToGameModuleName( path ):
	body, ext = os.path.splitext( path )
	return body.replace( '/', '.' )

##----------------------------------------------------------------##
def _isNewer( f1, f2 ):
	if os.path.exists( f1 ) and os.path.exists( f2 ):
		t1 = os.path.getmtime( f1 )
		t2 = os.path.getmtime( f2 )
		return t1 > t2
	else:
		return None

##----------------------------------------------------------------##
@task( 'CompileLuaScript' )
def taskCompileLuaScript( context, srcPath, dstPath, version = 'luajit', checktime = False ):
	compileLua( srcPath, dstPath, version, checktime )

@task( 'CompileLuaScriptAndRemoveSource' )
def taskCompileLuaScript( context, srcPath, dstPath, version = 'luajit', checktime = False ):
	compileLua( srcPath, dstPath, version, checktime )
	os.remove( srcPath )

##----------------------------------------------------------------##
_GII_SCRIPT_LIBRARY_EXPORT_NAME = 'script_library'

##----------------------------------------------------------------##

class LuaScriptAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.script'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name,ext = os.path.splitext(filepath)
		return ext in [ '.lua' ]

	def importAsset(self, node, reload = False ):
		node.assetType = 'lua'
		if reload:			
			lib = app.getModule( 'script_library' )
			lib.markModified( node )
			return True
		else:
			lib = app.getModule( 'script_library' )
			lib.loadScript( node )
			return True		

	def dropAsset( self , node ):
		lib = app.getModule( 'script_library' )
		lib.releaseScript( node )

	def getDefaultAssetDeployConfig( self, node ):
		return dict(
			package  = 'script',
			compress = False
		)

	def deployAsset( self, node, context ):
		#DO NOTHING, ScriptLibrary handles it
		pass

	def getMetaType( self ):
		return 'script'

##----------------------------------------------------------------##
class ScriptLibrary( EditorModule ):
	def getName( self ):
		return 'script_library'

	def getDependency( self ):
		return ['moai']

	def onLoad( self ):
		self.scripts = {}
		self.modifiedScripts = {}
		signals.connect( 'project.deploy', self.onDeploy )
		signals.connect( 'project.post_deploy', self.postDeploy )


	def convertScriptPath( self, node ):
		path = node.getNodePath()
		name, ext = os.path.splitext( path )
		return name.replace( '/', '.' )

	def markModified( self, node ):
		self.modifiedScripts[ node ] = True

	def isModified( self ):
		if self.modifiedScripts: return True
		return False

	def loadScript( self, node ):
		path = self.convertScriptPath( node )
		logging.info( 'loading script %s', path )
		m, err = _GII.GameModule.updateGameModule( path )
		if not m:
			for info in list(err.values()):
				logging.error( 'script error <%s>: %s', info.path, info.msg )

	def loadModifiedScript( self ):
		logging.info( 'reloading modified scripts' )
		modified = self.modifiedScripts
		self.modifiedScripts = {}
		load = False
		for node in modified:
			load = True
			self.loadScript( node )
		signals.emit( 'script.reload' )
		return load

	def releaseScript( self, node ):
		_GII.GameModule.unloadGameModule( self.convertScriptPath( node ) ) #force

	def onStart( self ):
		for node in self.getAssetLibrary().enumerateAsset( 'lua' ):
			_GII.GameModule.loadGameModule( self.convertScriptPath( node ) )

	def onDeploy( self, context ):
		version = context.getMeta( 'lua_version', 'lua' )
		scriptFormat = context.getMeta( 'script_format', 'source' )
		exportIndex = {}
		sourceIndex = {}
		count = 0
		
		print(('deploying lua scripts in format:', scriptFormat))
		with WorkerPool( worker_num = 8 ):
			for node in self.getAssetLibrary().enumerateAsset( 'lua' ):
				count += 1
				hashed = _hashPath( node.getFilePath() )
				# dstPath = context.getAssetPath( hashed )
				dstPath = context.requestFile( hashed, package = 'script' )
				exportIndex[ _convertToGameModuleName( node.getNodePath() ) ] = dstPath
				sourceIndex[ _convertToGameModuleName( node.getNodePath() ) ] = node.getNodePath()
				Task( 'CompileLuaScript' ).promise( context, node.getAbsFilePath(), context.getPath( dstPath ), scriptFormat, True )
				# _compileLuaScript( 
				# 	context, node.getAbsFilePath(), context.getPath( dstPath ), scriptFormat, True
				# )
				
		
		outputScriptIndex = context.requestFile( 
			_GII_SCRIPT_LIBRARY_EXPORT_NAME, 
			package = 'config'
		)

		JSONHelper.trySaveJSON(
				{
					'export' : exportIndex,
					'source' : sourceIndex
				}, 
				context.getAbsPath( outputScriptIndex ), 
				'script index' 
			)
		context.setMeta( 'mock_script_library', outputScriptIndex )


	def postDeploy( self, context ):
		#compile lib scripts
		scriptFormat = context.getMeta( 'script_format', 'source' )
		packageLib = context.affirmPackage( 'lib' )
		if not packageLib: return
		buildPath = packageLib.getBuildPath()
		if not os.path.isdir( buildPath ): return

		context.notify( ' > Compiling Lib Lua scripts ...' )
		#TODO: precompile libs
		srcRootPath = context.getProject().getGamePath( 'lib' )

		with WorkerPool():
			for root, dirs, files in os.walk( srcRootPath ):
				subDir = os.path.relpath( root, srcRootPath )
				buildRoot = buildPath + '/' + subDir
				_affirmPath( buildRoot )
				for f in files:
					if not f.endswith( '.lua' ): continue
					srcPath = root + '/' + f
					name, ext = os.path.splitext( f )
					# dstPath = root + '/' + name + '_'
					dstPath = buildRoot + '/' + name + '_'
					Task( 'CompileLuaScript' ).promise(
						context, srcPath, dstPath, scriptFormat, True
						)
				for d in dirs[:]:
					if d.startswith( '.' ):
						dirs.remove( d )
					# _compileLuaScript( context, srcPath, dstPath, scriptFormat, True )
					# os.remove( srcPath )

##----------------------------------------------------------------##
ScriptLibrary().register()
LuaScriptAssetManager().register()
##----------------------------------------------------------------##

class RemoteCommandReloadScript( RemoteCommand ):
	name = 'reload_script'
	def run( self, *args ):
		# app.getAssetLibrary().scheduleScanProject()
		app.getAssetLibrary().tryScanProject()
		lib = app.getModule( 'script_library' )
		lib.loadModifiedScript()
		giiSync = app.getModule( 'gii_sync_support' )
		if giiSync:
			giiSync.query( 'cmd.reload_script' )


class RemoteCommandReloadGameScript( RemoteCommand ):
	name = 'reload_game_script'
	def run( self, *args ):
		app.getAssetLibrary().tryScanProject()
		giiSync = app.getModule( 'gii_sync_support' )
		if giiSync:
			giiSync.query( 'cmd.reload_script' )
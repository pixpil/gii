import logging
import imp


from gii.core import *
from gii.qt             import SubEditorModule
from gii.moai.MOAIRuntime import MOAILuaDelegate


signals.register( 'script_command.register' )
##----------------------------------------------------------------##
class ScriptCommandMeta( type ):
	def __init__( cls, name, bases, dict ):
		super( ScriptCommandMeta, cls ).__init__( name, bases, dict )
		fullname = dict.get( 'name', None )
		if not fullname: return
		cmd = cls()
		ScriptCommandRegistry.get().registerCommand( fullname, cmd )

##----------------------------------------------------------------##
class ScriptCommand( object, metaclass=ScriptCommandMeta ):
	def run( self, args ):
		pass

##----------------------------------------------------------------##
class FunctionScriptCommand( ScriptCommand ):
	def __init__( self, func ):
		self._func = func

	def run( self, args ):
		return self._func( args )

# ##----------------------------------------------------------------##
# class ScriptCommandProvider(object):
# 	def process


##----------------------------------------------------------------##
class ScriptCommandRegistry( object ):
	_singleton = None

	@staticmethod
	def get():
		if not ScriptCommandRegistry._singleton:
			return ScriptCommandRegistry()
		return ScriptCommandRegistry._singleton

	def __init__( self ):
		ScriptCommandRegistry._singleton = self
		self.commands = {}

	def registerCommand( self, name, cmdObject ):
		signals.emit( 'script_command.register', name, cmdObject )
		self.commands[ name ] = cmdObject

	def doCommand( self, cmd, args ):
		if cmd:
			cmdObject = self.commands.get( cmd, None )
			if cmdObject:
				try:
					result = cmdObject.run( args )
					return result
				except Exception as e:
					logging.exception( e )
			else:
				logging.warning( 'no script command found:' + cmd )

ScriptCommandRegistry()

##----------------------------------------------------------------##
class ScriptCommandManager( SubEditorModule ):
	name = 'script_command_manager'
	dependency = [ 'qt' ]

	def onLoad( self ):
		self.menuNodes = {}
		self.scriptTimestamps = {}

	def onAppReady( self ):
		self.menu = self.addMenu( 'main/script', dict( label='Script' ) )
		self.addMenuItem( 'main/script/__refresh_script_commands__', dict( label='Refresh Commands' ) )
		self.addMenuItem( 'main/script/----' )

		self.scanCommandScripts()
		self.refreshMenu()
		signals.connect( 'script_command.register', self.onCommandRegister )

	def affirmMenuGroup( self, path ):
		if not path: return
		base = 'main/script/'
		currentMenu = self.menu
		for part in path.split( '/' ):
			nextMenu = currentMenu.findChild( part )
			if not nextMenu:
				nextMenu = currentMenu.addChild( dict( name = part, label = part, type = 'menu' ) )

	def refreshMenu( self ):
		self.clearMenu()
		registry = ScriptCommandRegistry.get()
		names = list(registry.commands.keys())
		base = 'main/script/'
		for name in sorted( names ):
			#affirm menu groups
			self.affirmMenuGroup( os.path.dirname( name ) )
			fullpath = base + name
			menuNode = self.addMenuItem( fullpath )
			self.menuNodes[ name ] = menuNode
			menuNode.scriptCommandName = name

	def clearMenu( self ):
		for key, menuNode in list(self.menuNodes.items()):
			menuNode.remove()
		self.menuNodes = {}

	def scanCommandScripts( self ):
		prj = Project.get()
		self.scanCommandScriptPath( app.getPath( 'support/commands' ) )
		self.scanCommandScriptPath( app.getUserPath( 'commands' ) )
		self.scanCommandScriptPath( prj.getEnvPath( 'commands' ) )
		print('done scanning command scripts.')

	def scanCommandScriptPath( self, path ):
		if not os.path.isdir( path ): return
		scripts = {}
		def walkPath( path ):
			for currentDir, dirs, files in os.walk( str(path) ):
				for dirname in dirs:
					fullpath = currentDir + '/' + dirname
					walkPath( fullpath )
				for filename in files:
					name, ext = os.path.splitext( filename )
					fullpath = currentDir + '/' + filename
					if ext == '.lua':
						self.loadCommandScriptLua( fullpath )

					elif ext == '.py':
						self.loadCommandScript( fullpath )

		walkPath( path )

	def loadCommandScript( self, path ):
		moduleName = 'command_script@' + path.replace( '\\', '/' ).replace( '/', '_' ).replace( '.', '_' )
		mtime0 = self.scriptTimestamps.get( path, 0 )
		mtime1 = os.path.getmtime( path )
		if mtime1 <= mtime0: return #ignore
		self.scriptTimestamps[ path ] = mtime1
		try:
			print('loading command script:', path)
			m = imp.load_source( moduleName, path )
		except Exception as e:
			logging.warning( 'failed loading command script:' + path )
			logging.exception( e )
			return False

		if not hasattr( m, 'name' ):
			logging.warning( 'no command name provided in command script:' + path )
			return False
		name = m.name
		if hasattr( m, 'run' ):
			run = m.run
			cmdObject = FunctionScriptCommand( run )
			ScriptCommandRegistry.get().registerCommand( name, cmdObject )
		return True

	def loadCommandScriptLua( self, path ):
		print('loading lua command script', path)
		mtime0 = self.scriptTimestamps.get( path, 0 )
		mtime1 = os.path.getmtime( path )
		if mtime1 <= mtime0: return #ignore
		self.scriptTimestamps[ path ] = mtime1
		
		delegate = MOAILuaDelegate( self )
		if not delegate.load( path ):
			return False
		
		name = delegate.getEnv( 'name' )
		run  = delegate.getEnv( 'run' )
		if name and run:
			cmdObject = FunctionScriptCommand( run )
			ScriptCommandRegistry.get().registerCommand( name, cmdObject )
		return True


	def onCommandRegister( self, name, clas ):
		self.refreshMenu()

	def onMenu(self, node):
		if node.name == '__refresh_script_commands__':
			self.scanCommandScripts()
		else:
			cmdName = node.scriptCommandName		
			registry = ScriptCommandRegistry.get()
			registry.doCommand( cmdName, None )

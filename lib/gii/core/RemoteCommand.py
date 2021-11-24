import logging

class RemoteCommandMeta( type ):
	def __init__( cls, name, bases, dict ):
		super( RemoteCommandMeta, cls ).__init__( name, bases, dict )
		fullname = dict.get( 'name', None )
		if not fullname: return
		RemoteCommandRegistry.get().registerCommand( fullname, cls )

##----------------------------------------------------------------##

##----------------------------------------------------------------##
class RemoteCommand( object, metaclass=RemoteCommandMeta ):
	def run( self, argv ):
		pass

# ##----------------------------------------------------------------##
# def RemoteFunc( name ):
# 	def wrapperFunc( func ):
# 		class AnonymousCommand( RemoteCommand ):
# 			def run( argv ):
# 				return func( argv )
# 		RemoteCommandRegistry.get().registerCommand( name, AnonymousCommand )
# 	return wrapperFunc

##----------------------------------------------------------------##
class RemoteCommandRegistry( object ):
	_singleton = None

	@staticmethod
	def get():
		if not RemoteCommandRegistry._singleton:
			return RemoteCommandRegistry()
		return RemoteCommandRegistry._singleton

	def __init__( self ):
		RemoteCommandRegistry._singleton = self
		self.commands = {}

	def registerCommand( self, name, cmdClas ):
		self.commands[ str(name) ] = cmdClas

	def doCommand( self, argv, output ):
		if argv:
			strArgv = [ str( v, encoding = 'utf-8' ) for v in argv ]
			cmdName = strArgv[ 0 ]
			clas = self.commands.get( cmdName, None )
			if clas:
				cmd = clas()
				if len( argv ) > 1 :
					args = strArgv[1:]
				else:
					args = []
				try:
					result = cmd.run( *args )
					output.append( result )
				except Exception as e:
					logging.exception( e )
			else:
				logging.warning( 'no remote command found:' + cmdName )


RemoteCommandRegistry()


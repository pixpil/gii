from .RemoteCommand import *
from .guid import generateGUID
import msgpack

import re
from . import signals

import base64
import logging


def processGiiURL( url ):
	url = url.strip()
	if url.startswith( 'gii://' ):
		mo = re.match( 'gii://(\w+)/(.*)', url )
		if not mo:
			logging.warning( 'invalid URL: ' + str(url) )
			return False
		base = mo.group(1)
		data64 = mo.group(2)
		datastr = base64.b64decode( bytes(data64, encoding = 'ascii' ) )
		try:
			data = msgpack.loads( datastr, encoding = "utf-8" )
		except Exception as e:
			logging.warning( 'invalid URL data.' )
			print( e )
			return False
		v = {
			'base' : base,
			'data' : data,
			'raw'  : url
		}
		print( 'processing url:', v )
		signals.emit( 'app.open_url', v )

##----------------------------------------------------------------##
class RemoteCommandOpenURL( RemoteCommand ):
	name = 'open_url'		
	def run( self, *args ):
		if args:
			url = args[0]
			if not isinstance( url, str ): return
			processGiiURL( url )
		else:
			print('no URL')

##----------------------------------------------------------------##
def encodeGiiURL( base, data ):
	if isinstance( data, dict ):
		datastr = msgpack.dumps( data, encoding = "utf-8" )
		encoded = base64.b64encode( datastr )
		return 'gii://' + str(base) + '/' + str(encoded, encoding='ascii')
	else:
		raise Exception( 'dict expected for url data' )

# ##----------------------------------------------------------------##
# class URLHandlerMeta( type ):
# 	def __init__( cls, name, bases, dict ):
# 		super( URLHandlerMeta, cls ).__init__( name, bases, dict )
# 		fullname = dict.get( 'name', None )
# 		if not fullname: return
# 		URLHandlerRegistry.get().registerCommand( fullname, cls )

# ##----------------------------------------------------------------##

# ##----------------------------------------------------------------##
# class URLHandler( object ):
# 	__metaclass__ = URLHandlerMeta
# 	def run( self, argv ):
# 		pass


# ##----------------------------------------------------------------##
# class URLHandlerRegistry( object ):
# 	_singleton = None

# 	@staticmethod
# 	def get():
# 		if not URLHandlerRegistry._singleton:
# 			return URLHandlerRegistry()
# 		return URLHandlerRegistry._singleton

# 	def __init__( self ):
# 		URLHandlerRegistry._singleton = self
# 		self.handlers = {}

# 	def registerCommand( self, name, cmdClas ):
# 		self.handlers[ name ] = cmdClas

# 	def doCommand( self, argv, output ):
# 		if argv:
# 			cmdName = argv[0]
# 			clas = self.handlers.get( cmdName, None )
# 			if clas:
# 				cmd = clas()
# 				if len( argv ) > 1 :
# 					args = argv[1:]
# 				else:
# 					args = []
# 				try:
# 					result = cmd.run( *args )
# 					if isinstance( result, ( str, unicode ) ):
# 						output.append( result.encode('utf-8') )
# 				except Exception, e:
# 					logging.exception( e )
# 			else:
# 				logging.warning( 'no remote command found:' + cmdName )


# URLHandlerRegistry()


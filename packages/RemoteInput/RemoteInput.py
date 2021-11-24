import os
import stat
import logging

from gii.core import *
from . import WebHTTPServer
from . import WebSocketServer

signals.register( 'remote_input.received' )

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

class RemoteInputServer( EditorModule ):
	name = 'remote_input_server'
	dependency = []

	def onLoad( self ):
		self.baseTouchID = 3
		scriptPath     = _getModulePath( 'InputSender.lua' )
		self.delegate  = app.getModule('moai').loadLuaDelegate( scriptPath )		
		signals.connect(  'remote_input.received', self.onRemoteInput )

	def onStart( self ):
		WebHTTPServer.startServer()
		WebSocketServer.startServer( self.onSocketData )
		
	def onStop( self ):
		WebHTTPServer.stopServer()
		WebSocketServer.stopServer()

	def onRemoteInput( self, msg ):
		self.delegate.call( 'sendInput', msg['event'], msg['id'], msg['x'], msg['y'], msg['z'] )

	def onSocketData( self, data ):
		data = str( data )
		if not data and data[0]=='@': return
		items = str(data[1:]).split( ',' )
		ev = items[0]
		msg = {
			"event" : items[0],
			"id" : int( items[1] ),
			"x"  : int( items[2] ),
			"y"  : int( items[3] ),
			"z"  : int( items[4] )
		}
		signals.emit( 'remote_input.received', msg )
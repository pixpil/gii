import os
import logging
import argparse
import socket
import base64
import json
import subprocess

from gii.core import *
from gii.core.InstanceHelper import send_to_server

_GII_SUBLIME_PORT = 61958
_HOST = '127.0.0.1'

def encodeData( data ):
	return base64.b64encode( json.dumps( data ).encode( 'utf-8') )

def decodeData( data ):
	return json.loads( str( base64.b64decode( data ), encoding= 'utf-8' ) )

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

def findSubl():
	#TODO
	return 'subl'

##----------------------------------------------------------------##
class SublimeRemote( EditorModule ):
	name = 'sublime_remote'
	dependency = []

	def onStart( self ):
		pass

	def openFile( self, path, linenumber = None ):
		path = os.path.abspath( path )
		sublPath = findSubl()
		if not sublPath:
			logging.warning( '"subl" not found' )
			return
		subprocess.call( [ sublPath, path ]  )
		self.sendCommand( 'open', path, linenumber )

	def sendCommand( self, cmd, *args ):
		data = {
			'cmd': cmd,
			'args': args
		}
		encoded = encodeData( data )
		send_to_server( _HOST, _GII_SUBLIME_PORT, encoded )

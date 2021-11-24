from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import time
import threading
import logging

_HTTP_PORT = 8030

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class Handler(BaseHTTPRequestHandler):

	def do_GET(self):
		self.send_response(200)
		self.end_headers()
		if self.path == '/':
			f = open( _getModulePath( 'main.htm' ), 'r' )
			txt = f.read()
			f.close()
			self.wfile.write( txt )
		return

	def log_message( self, format, *ars ):
		pass

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""    

_Running = False

def _startServer():
	global _Running
	server = ThreadedHTTPServer(('0.0.0.0', _HTTP_PORT), Handler)
	_Running = True
	server.timeout = 0
	logging.info( 'start remote input listener at port: %d' % _HTTP_PORT )
	while _Running:
		server.handle_request()
		time.sleep(0.1)


def startServer():
	threading.Thread( target = _startServer ).start()

def stopServer():
	global _Running
	_Running = False
	logging.info( 'stopping remote input listener at port: %d' % _HTTP_PORT )
	
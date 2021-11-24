import time
import threading
import logging
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer

_WS_PORT = 8037
_onMessage = None

class WebSocketHandler(WebSocket):

	def handleMessage(self):
		if self.data is None:
			self.data = ''
		# echo message back to client
		# self.sendMessage(str(self.data))
		if _onMessage: _onMessage( self.data )
		self.sendMessage( '' ) #roger

	def handleConnected(self):
		print(self.address, 'connected')

	def handleClose(self):
		print(self.address, 'closed')



_Running = False

def _startServer():
	global _Running
	server = SimpleWebSocketServer( '' , _WS_PORT, WebSocketHandler)
	_Running = True
	logging.info( 'start remote input socket listener at port: %d' % _WS_PORT )
	while _Running:
		server.handleRequest()
		time.sleep(0.003)

def startServer( messageCallback ):
	global _onMessage
	threading.Thread( target = _startServer ).start()
	_onMessage = messageCallback

def stopServer():
	global _Running
	_Running = False
	logging.info( 'stopping remote input socket listener at port: %d' % _WS_PORT )
	
import sys
import logging
import os
import socketserver
import socket
import threading
from time import sleep

RemoteArgumentCallBack=None
_GII_INSTANCE_PORT = 61957
_GII_RPC_PORT = 0x6A37

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
	def handle(self):
		data = self.request.recv(65535)
		cur_thread = threading.currentThread()
		logging.info('remote data:' + str( data, encoding='utf-8' ) )
		data = data.split()
		#Note to the self.server.app
		output = []
		if not RemoteArgumentCallBack is None:
			RemoteArgumentCallBack( data, output )
		bytesOutput = []
		for out in output:
			if isinstance( out, str ):
				bytesOutput.append( bytes( out, encoding = 'utf-8' ) )
			elif isinstance( out, bytes ):
				bytesOutput.append( out )
			else:
				pass

		if bytesOutput:
			result = b'\n'.join( bytesOutput )
		else:
			result = b''
		self.request.send( result )
		logging.info('remote command result: %s' % result )

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	stopped = False
	allow_reuse_address = True

	def serve_forever(self):
		while not self.stopped:
			self.handle_request()

	def force_stop(self):
		self.server_close()
		self.stopped = True

def send_to_server(ip, port, message, **option ):
	# import syslog
	if not port:
		port = _GII_INSTANCE_PORT
	# syslog.openlog("Gii")
	# syslog.syslog( syslog.LOG_ALERT, "create socket")
	# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock = socket.socket()
	sock.settimeout( option.get( 'connect_timeout', 0.02 ) )
	# syslog.syslog( syslog.LOG_ALERT, "connecting")

	result = sock.connect((ip, port))
	sock.settimeout( option.get( 'message_timeout', 1 ) )

	# syslog.syslog( syslog.LOG_ALERT, "sending")
	if isinstance( message, str ):
		message = bytes( message, encoding='utf-8' )

	sock.send( message )
	response = sock.recv(65535)
	sock.close()
	return response

def start_server(host, port):

	server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)
	ip, port = server.server_address

	# Start a thread with the server -- that thread will then start one
	# more thread for each request
	server_thread = threading.Thread(target=server.serve_forever)
	# Exit the server thread when the main thread terminates
	server_thread.setDaemon(True)
	server_thread.start()

	return server

def send_to_rpc_server( **options ):
	host = options.get( 'host', 'localhost' )
	port = options.get( 'port', _GII_RPC_PORT )
	import rpyc
	try:
		print(('connecting to %s : %s' % ( host, port )))
		conn = rpyc.classic.connect( host, port )
		remoteGii = conn.modules.gii
		msgs = options.get( 'messages' )
		print(('running:', msgs))
		print('-------------------')
		print()
		proc, stdOutQueue, stdErrQueue = remoteGii.startSubProcess( msgs )
		sleep( 0.1 )
		stdout = sys.stdout
		stderr = sys.stderr
		while proc.poll() is None:
			batchEmpty = True
			while True:
				empty = True
				try:
					line = stdOutQueue.get_nowait() # or q.get(timeout=.1)
				except Exception as e:
					pass
				else: # got line
					empty = False
					stdout.write( line )
					stdout.flush()

				try:
					line = stdErrQueue.get_nowait() # or q.get(timeout=.1)
				except Exception as e:
					pass
				else: # got line
					empty = False
					stderr.write( line )
					stderr.flush()

				if not empty:
					batchEmpty = False
				else:
					break
			#end while
			if batchEmpty:
				sleep( 0.01 )

		print()
		print('-------------------')
		print('done')

	except Exception as e:
		print(e)
		print('failed to connect to remote server')
		return False
	return True


def start_rpc_server( **options ):
	host = options.get( 'host', '0.0.0.0' )
	port = options.get( 'port', _GII_RPC_PORT )
	import rpyc
	from rpyc.core import SlaveService
	from rpyc.lib import setup_logger
	setup_logger()

	import locale
	encoding = options.get( 'encoding', locale.getpreferredencoding() )
	os.environ[ 'GII_RPC_STDIO_ENCODING' ] = encoding
	try:
		print( 'starting RPC server', host, port, encoding )
		server = rpyc.utils.server.ThreadedServer(
			SlaveService, port=port, hostname=host, reuse_addr = True
		)   
		server.start()
	except Exception as e:
		print(e)
		return False

server = None
def checkSingleInstance(PORT=0):
	if PORT == 0:
		PORT = _GII_INSTANCE_PORT
	# HOST = socket.gethostname()
	HOST = '127.0.0.1'
	argv=sys.argv[:]
	argv.insert(0, os.path.realpath('.'))
	# if len(argv) > 1:
	#     argv[1]=os.path.realpath(argv[1])
	try:
		send_to_server(HOST, PORT, ' '.join(argv)) #send a message to server
		return False        
	except socket.error: #port not occupied, it's safe to start a new instance
		server = start_server(HOST, PORT)
		return True

def setRemoteArgumentCallback(callback):
	global RemoteArgumentCallBack
	RemoteArgumentCallBack=callback

def sendRemoteMsg( msg ):
	PORT = _GII_INSTANCE_PORT
	HOST = '127.0.0.1'
	response = send_to_server( HOST, PORT, msg )
	return response
	
import sublime, sublime_plugin
import base64
import sys
import logging
import os
import socketserver
import socket
import threading
import json

RemoteArgumentCallBack=None
_GII_SUBLIME_PORT = 61958

def encodeData( data ):
    return base64.b64encode( json.dumps( data ).encode( 'utf-8' ) )

def decodeData( data ):
    s = str( base64.b64decode( data ), 'utf-8' )
    return json.loads( s )


def getArg( arg, i, default = None ):
    v = None
    if len( arg ) > i:
        v = arg[ i ]
    if v == None:
        return default
    else:
        return v

def doCommand( cmd, args ):
    if cmd == 'open':
        path = getArg( args, 0 )
        line = getArg( args, 1, 0 )
        fullpath = '%s:%d' % ( path, line )
        sublime.active_window().open_file( fullpath, sublime.ENCODED_POSITION )

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            raw = self.request.recv(65535)
            cur_thread = threading.currentThread()
            data = decodeData( raw )
            cmd = data.get( 'cmd', None )
            args = data.get( 'args', [] )
            if cmd:
                doCommand( cmd, args )
            self.request.send( encodeData( { 'response': 'ok' } ) )
        except Exception as e:
            print( e )

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    stopped = False
    allow_reuse_address = True

    def serve_forever(self):
        while not self.stopped:
            self.handle_request()

    def force_stop(self):
        self.stopped = True
        self.server_close()

def send_to_server(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    sock.send(message)
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

##----------------------------------------------------------------##

server = None
HOST = '127.0.0.1'
PORT = _GII_SUBLIME_PORT

def plugin_loaded():
    print( 'start Gii RemoteListener' )
    global server
    server = start_server( HOST, PORT )

def plugin_unloaded():
    print( 'stop Gii RemoteListener' )
    global server
    server.force_stop()


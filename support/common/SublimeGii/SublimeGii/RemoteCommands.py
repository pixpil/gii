import sys
import logging
import os
import socket
import time
import sublime_plugin
import sublime
import json
import base64


def send_to_server( message = '', ip = '127.0.0.1', port = 61957 ):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout( 0.01 )
	sock.connect((ip, port))
	sock.settimeout( 0.1 )
	sock.send( message.encode('utf-8') )
	response = sock.recv( 1048576 )
	sock.close()
	return response

def encodeData( data ):
	return base64.b64encode( json.dumps( data ).encode( 'utf-8' ) )

def decodeData( data ):
	s = str( base64.b64decode( data ), 'utf-8' )
	return json.loads( s )


def encodeStr( s ):
	return str( base64.b64encode( bytes( s, 'utf-8' ) ), 'ascii' )

def decodeStr( data ):
	s = str( base64.b64decode( data ), 'utf-8' )
	return s

class GiiSendRemoteCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		self.kwargs = kwargs
		sublime.active_window().show_input_panel('Command to send:', '', self.do, None, None)

	def do(self, command):
		kwargs = self.kwargs
		kwargs['cmd'] = command
		send_to_server( command )


class GiiReloadScriptCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		send_to_server( 'reload_script' )

class GiiReloadGameScriptCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		send_to_server( 'reload_game_script' )

class GiiRunGameCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		send_to_server( 'run_game' )


class GiiEvalCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		sublime.active_window().show_input_panel('(Gii)Script to execute:', '', self.do, None, None)

	def do(self, script):
		send_to_server( 'eval '+ encodeStr( script ))


class GiiEvalViewRemoteCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		# sublime.active_window().show_input_panel('(Gii)Argument:', '', self.do, None, None)
		view = sublime.active_window().active_view()
		if not view:
			sublime.error_message( 'no active view!' )
			return

		# if sublime.ok_cancel_dialog( 'Eval current script in Gii?' ):
		source = view.substr(sublime.Region(0, view.size()))
		# source = source.replace('"', '\\"')
		# source = source.replace("'", "\\'")
		# print( source )
		# source = source.encode('unicode-escape').replace('"', '\\"')
		# source = source.encode( 'utf-8' )
		send_to_server( 'eval_remote ' + encodeStr( source ))
		sublime.status_message( 'gii script executed')

	# def do(self, script):
	# 	send_to_server( 'eval '+script )
	

class GiiEvalViewCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		# sublime.active_window().show_input_panel('(Gii)Argument:', '', self.do, None, None)
		view = sublime.active_window().active_view()
		if not view:
			sublime.error_message( 'no active view!' )
			return

		# if sublime.ok_cancel_dialog( 'Eval current script in Gii?' ):
		source = view.substr(sublime.Region(0, view.size()))
		# source = source.replace('"', '\\"')
		# source = source.replace("'", "\\'")
		# print( source )
		# source = source.encode('unicode-escape').replace('"', '\\"')
		# source = source.encode( 'utf-8' )
		send_to_server( 'eval ' + encodeStr( source ))
		sublime.status_message( 'gii script executed')

	# def do(self, script):
	# 	send_to_server( 'eval '+script )
	

class GiiPreviewStartCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		sublime.active_window().run_command( 'save_all' )
		time.sleep(0.1)
		send_to_server( 'reload_script' )
		time.sleep(0.2)
		send_to_server( 'preview_start' )


class GiiPreviewStopCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		send_to_server( 'preview_stop' )


class GiiRunGameCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		sublime.active_window().run_command( 'save_all' )
		send_to_server( 'run_game' )		

class GiiRunSceneCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		sublime.active_window().run_command( 'save_all' )
		send_to_server( 'run_scene' )		

class GiiStopExternRunCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		send_to_server( 'stop_extern_run' )

##----------------------------------------------------------------##
class GiiStartControlSessionCommand(sublime_plugin.WindowCommand):
	def run(self, **kwargs):
		self.kwargs = kwargs
		result = send_to_server( 'control_session_start' )
		self.processResult( result )

	def processResult( self, result ):
		if result:
			data = decodeData( result )
			answer = data.get( 'answer', None )
			print( data )
			if answer == 'end':
				return
				
			elif answer == 'error':
				sublime.error_message( 'error occurs!' )
				return

			elif answer == 'files':
				self.fileItems = data[ 'files' ]
				self.sessionId = data[ 'session_id' ]
				fileNames = [ fileItem['name'] for fileItem in self.fileItems ]
				sublime.active_window().show_quick_panel( fileNames, self.onFileSelected )

			else: #list
				self.items = data[ 'items' ]
				self.sessionId = data[ 'session_id' ]
				itemNames = [ item['name'] for item in self.items ]
				sublime.active_window().show_quick_panel( itemNames, self.onCommandSelected )

		else:
			sublime.error_message( 'gii not responsing!' )

	def onCommandSelected( self, selected ):
		if selected < 0 : return
		view = sublime.active_window().active_view()
		context = {}
		if view:
			line = 0
			for sel in view.sel():
				line, col = view.rowcol(sel.a)
			context[ 'source' ] = {
				'file' : view.file_name(),
				'line' : line + 1
			}
		else:
			context[ 'source' ] = False
		response = {
			'session_id' : self.sessionId,
			'index'    : selected,
			'context'  : context
		}
		result = send_to_server( 'control_session_send'+' '+str(encodeData( response ),'ascii') )
		self.processResult( result )

	def onFileSelected( self, selected ):
		if selected < 0 : return
		fileItem = self.fileItems[ selected ]
		path = fileItem[ 'path' ]
		sublime.active_window().open_file( path )


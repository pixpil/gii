import random
import os
import os.path
import shutil
import logging

from .QtSupport import *
from .QtEditorModule import *
from gii.core.EditorModule import EditorModuleManager
from gii.qt.dialogs   import requestString, alertMessage, requestConfirm

from gii.SearchView       import requestSearchView, registerSearchEnumerator

WINDOW_SCHEME_EXTENSION = '.window_scheme'
WINDOW_SCHEME_BASE_PATH = 'WindowSchemes'

##----------------------------------------------------------------##
def _affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False

class QtWindowScheme(object):
	def __init__( self, id ):
		self.id   = id or generateGUID()
		self.name = None
		self.arg  = arg
		

class QtWindowSchemeManager( QtGlobalModule ):
	name = 'qt_window_scheme_manager'
	dependency = [ 'qt' ]

	def onLoad( self ):
		self.schemes = []
		self.activeScheme = None
		self.schemeBasePath = self.getProject().getWorkspacePath( WINDOW_SCHEME_BASE_PATH )
		_affirmPath( self.schemeBasePath )

		self.findMenu( 'main/window' ).addChild([
			dict( name = 'save_scheme', label = 'Save Scheme', shortcut = 'Shift+F4' ),
			dict( name = 'load_scheme', label = 'Load Scheme', shortcut = 'F4' )
		], self )

	def onStart( self ):
		self.loadWindowSchemeFromFile( '__default' )

	def onStop( self ):
		self.saveWindowSchemeToFile( '__default' )

	def saveWindowScheme( self ):
		queue = EditorModuleManager.get().affirmSortedModuleQueue()
		scheme = {}
		for m in queue:
			if isinstance( m, QtEditorModule ):
				data = m.saveWindowState2()
				if data:
					scheme[ m.getName() ] = data
		return scheme

	def loadWindowScheme( self, scheme ):
		queue = EditorModuleManager.get().affirmSortedModuleQueue()
		for m in queue:
			if isinstance( m, QtEditorModule ):
				name = m.getName()
				data = scheme.get( name, None )
				if data:
					m.loadWindowState2( data )

	def loadWindowSchemeFromFile( self, name ):
		path = self.schemeBasePath + '/' + name
		if os.path.isfile( path ):
			data = JSONHelper.tryLoadJSON(
				path,
				'window scheme data'
			)
			if data:
				self.loadWindowScheme( data )
		else:
			logging.warning( 'no window scheme data found: ' + name )


	def saveWindowSchemeToFile( self, name ):
		data = self.saveWindowScheme()
		path = self.schemeBasePath + '/' + name
		JSONHelper.trySaveJSON(
			data,
			path,
			'window scheme data'
		)

	def scanWindowSchemeFiles( self ):
		result = []
		for filename in os.listdir( self.schemeBasePath ):
			name, ext = os.path.splitext( filename )
			if ext != WINDOW_SCHEME_EXTENSION : continue
			if name.startswith( '__' ): continue
			result.append( ( name, name, 'Window Scheme', 'file' )  )
		return result

	def prompLoadScheme( self ):
		entries = self.scanWindowSchemeFiles()
		def _changeScheme( name ):
			filepath = name + WINDOW_SCHEME_EXTENSION
			self.loadWindowSchemeFromFile( filepath )
	
		requestSearchView( 
			info         = 'choose window scheme',
			selections   = entries,
			on_selection = _changeScheme
		)

	def onMenu( self, menuNode ):
		name = menuNode.name
		if name == 'save_scheme':
			name = requestString( 'Save Window Scheme', 'Enter Scheme Name' )
			if not name: return
			self.saveWindowSchemeToFile( name + WINDOW_SCHEME_EXTENSION )

		elif name == 'load_scheme':
			self.prompLoadScheme()

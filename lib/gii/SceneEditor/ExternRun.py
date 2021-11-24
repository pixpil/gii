import logging

from gii.core import *
from gii.core.tools import RunHost

from qtpy import QtWidgets, QtGui,QtCore, uic
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox

import threading
import time

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

DialogForm,BaseClass = uic.loadUiType( _getModulePath('ExternRun.ui') )


##----------------------------------------------------------------##
def _formatSeconds( seconds ):
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	return "%d:%02d:%02d" % (h, m, s)

##----------------------------------------------------------------##
_currentExternRunDialog = None

class ExternRunDialog( QtWidgets.QDialog ):
	def __init__( self, targetName, **kwargs ):
		global _currentExternRunDialog
		super( ExternRunDialog, self ).__init__( **kwargs )
		_currentExternRunDialog = self
		self.ui = DialogForm()
		self.ui.setupUi( self )
		self.targetName = targetName
		self.playerThread = ExternRunThread( self.targetName )
		self.finished = False
		

		self.timer = QtCore.QTimer( self )
		self.timer.setInterval( 50 )
		self.timer.timeout.connect( self.onTimerTick )
		self.timer.start()

		self.startTime = time.time()

		self.ui.buttonTerminate.clicked.connect( self.onButtonTerminate )

		# self.setWindowModality( Qt.ApplicationModal )
		# self.setWindowModality( Qt.WindowModal )
		# self.setWindowFlags( Qt.Window | Qt.WindowStaysOnTopHint )
		# self.setWindowFlags( Qt.Tool )

		self.show()
		self.raise_()
		self.playerThread.start()
		
		signals.emitNow( 'external_player.start', targetName )


	def setMessage( self, msg ):
		self.ui.labelMessage.setText( msg )

	def onTimerTick( self ):
		elapsed = time.time() - self.startTime
		self.ui.labelElapsed.setText( 'Elapsed: ' + _formatSeconds( elapsed ) )
		if self.playerThread.finished: 
			self.timer.stop()
			self.onFinish()

	def onFinish( self ):
		self.ui.buttonTerminate.setText( 'OK' )
		self.finished = True
		self.setWindowModality( Qt.NonModal )
		self.setMessage( 'Finished' )
		if self.ui.checkAutoClose.isChecked():
			self.hide()
			self.close()
		signals.emitNow( 'external_player.stop' )

	def onButtonTerminate( self ):
		if self.finished:
			self.close()
		else:
			RunHost.terminate()
			self.playerThread.finished = True
			self.ui.buttonTerminate.setEnabled( False )

	def closeEvent( self ,ev ):
		if not self.finished: return
		global _currentExternRunDialog
		_currentExternRunDialog = None
		return super( ExternRunDialog, self ).closeEvent( ev )

##----------------------------------------------------------------##
class ExternRunThread( threading.Thread ):
	def __init__( self, targetName ):
		super( ExternRunThread, self ).__init__()
		self.targetName = targetName
		self.finished = False

	def run( self ):
		if not self.targetName:
			return
		returncode = RunHost.run( self.targetName )
		self.finished = True


##----------------------------------------------------------------##
def runScene( scnPath, **kwargs ):
	if _currentExternRunDialog:
		_currentExternRunDialog.show()
		_currentExternRunDialog.raise_()
		return
	app.getProject().save()
	app.getAssetLibrary().saveAssetIndexOutput()
	parentWindow = kwargs.get( 'parent_window', None )
	dialog = ExternRunDialog( 'main_preview_scene', parent = parentWindow )
	dialog.setMessage( 'Running current scene' )
	dialog.setWindowTitle( 'Running current scene' )

def runGame( **kwargs ):
	if _currentExternRunDialog:
		_currentExternRunDialog.show()
		_currentExternRunDialog.raise_()
		return
	app.getProject().save()
	app.getAssetLibrary().saveAssetIndexOutput()
	parentWindow = kwargs.get( 'parent_window', None )
	dialog = ExternRunDialog( 'main', parent = parentWindow )
	dialog.setMessage( 'Running game' )
	dialog.setWindowTitle( 'Running game' )

def stopExternRun():
	if _currentExternRunDialog:
		_currentExternRunDialog.onButtonTerminate()
		_currentExternRunDialog.close()

import logging
from qtpy import QtWidgets, QtGui,QtCore, uic
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox

import threading


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

ProcessDialogForm,BaseClass = uic.loadUiType( _getModulePath('ProcessDialog.ui') )

class ProcessDialog( QtWidgets.QFrame ):
	def __init__( self, *args, **kwargs ):
		super( ProcessDialog, self ).__init__( *args, **kwargs )
		self.ui = ProcessDialogForm()
		self.ui.setupUi( self )
		self.setWindowFlags( Qt.Dialog )

def requestProcess( message, **options ):
	dialog = ProcessDialog()

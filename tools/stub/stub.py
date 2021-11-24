import os.path
import logging
from . import osbit

from gii.core import Project, app
from gii.qt.helpers   import addWidgetWithLayout
from gii.qt.dialogs   import alertMessage
from gii.qt.IconCache   import getGiiIcon
from qtpy    import QtWidgets, QtGui, QtCore, uic
##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
##----------------------------------------------------------------##
_task = {
	'task' : False,
	'path' : '',
	'option' : {}
}
##----------------------------------------------------------------##
class StubGui( QtWidgets.QWidget ):
	def __init__( self ):
		QtWidgets.QWidget.__init__( self )
		self.ui = addWidgetWithLayout( 
			uic.loadUi( _getModulePath( 'stub.ui' ) ),
			self
		)
		self.setMinimumSize( 600,400 )
		self.setMaximumSize( 600,400 )

		self.ui.buttonOpen.clicked.connect( self.onButtonOpen )
		self.ui.buttonNew.clicked.connect( self.onButtonNew )

		self.setWindowTitle( 'GII ( %d bits )' % osbit.pythonBits() )

	def onButtonNew( self ):
		alertMessage ( 'Not implemented','Not implemented yet, use CLI instead.')

	def onButtonOpen( self ):
		options   = QtWidgets.QFileDialog.DontResolveSymlinks | QtWidgets.QFileDialog.ShowDirsOnly
		path      = QtWidgets.QFileDialog.getExistingDirectory(self,
			"Select Project Folder To Open",
			"",
			options
			)		
		if path:
			projectPath, info = Project.findProject( path )
			if projectPath:
				_task[ 'task' ] = 'open'
				_task[ 'path' ] = projectPath
				self.close()
			else:
				alertMessage( 'Project not found','No valid Gii project found.' )				

##----------------------------------------------------------------##
def start():
	import platform

	stubApp = QtWidgets.QApplication( [] )
	if platform.system() != 'Darwin':
		stubApp.setWindowIcon( getGiiIcon() )
	gui = StubGui()
	gui.show()
	gui.raise_()
	stubApp.exec_()
	return _task

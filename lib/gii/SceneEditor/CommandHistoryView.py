import random
##----------------------------------------------------------------##
from gii.core        import app, signals
from gii.core.Command import EditorCommandRegistry

from gii.qt          import QtEditorModule
from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericListWidget import GenericListWidget

from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

def _fixDuplicatedName( names, name, id = None ):
	if id:
		testName = name + '_%d' % id
	else:
		id = 0
		testName = name
	#find duplicated name
	if testName in names:
		return _fixDuplicatedName( names, name, id + 1)
	else:
		return testName

##----------------------------------------------------------------##
class CommandHistoryView( SceneEditorModule ):
	name = 'command_history_view'
	dependency = [ 'scene_editor' ]
	def onLoad( self ):
		#UI
		self.window = self.requestDockWindow( 'CommandHistoryView',
			title     = 'History',
			size      = (100,50),
			minSize   = (50,50),
			dock      = 'left'
			)

		#Components
		self.listHistory = self.window.addWidget( 
				CommandHistoryListWidget( 
					multiple_selection = False,
					editable           = False,
					drag_mode          = False
				)
			)
		self.listHistory.parentModule = self

		signals.connect( 'command.new',  self.onCommandNew )
		signals.connect( 'command.redo', self.onCommandRedo )
		signals.connect( 'command.undo', self.onCommandUndo )

	def onStart( self ):
		registry = EditorCommandRegistry.get()
		self.targetStack = registry.getCommandStack( 'scene_editor' )
		self.listHistory.clear()

	def getHistoryCommands( self ):
		return self.targetStack.undoStack

	def updateList( self ):
		self.listHistory.rebuild()

	def onCommandNew( self, cmd, cmdStack ):
		if cmdStack != self.targetStack: return
		self.listHistory.addNode( cmd )

	def onCommandRedo( self, cmd, cmdStack ):
		if cmdStack != self.targetStack: return
		self.listHistory.addNode( cmd )

	def onCommandUndo( self, cmd, cmdStack ):
		if cmdStack != self.targetStack: return
		self.listHistory.removeNode( cmd )



	
##----------------------------------------------------------------##
class CommandHistoryListWidget( GenericListWidget ):
	def getNodes( self ):
		return self.parentModule.getHistoryCommands()

	def updateItemContent( self, item, node, **options ):
		item.setText( repr(node) )


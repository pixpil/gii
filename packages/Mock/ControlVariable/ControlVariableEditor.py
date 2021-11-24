from gii.core import  *
from gii.SceneEditor.Introspector   import ObjectEditor, registerObjectEditor
from gii.qt.controls.PropertyEditor import PropertyEditor
from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter

from qtpy import QtWidgets, QtGui, QtCore, uic
from qtpy.QtCore import Qt
from qtpy.QtCore import QEventLoop, QEvent, QObject


from mock import _MOCK, isMockInstance, getMockClassName


##----------------------------------------------------------------##
def getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class ControlVariableSetTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **options ):
		options[ 'editable' ] = True
		super( ControlVariableSetTreeWidget, self ).__init__( *args, **options )
		self.target = None
		self.setIndentation( 0 )

	def setTarget( self, target ):
		self.target = target
		self.rebuild()

	def getHeaderInfo( self ):
		return [ ('ID',150, True ), ('Value', 80, True ), ('Desc',-1, True) ]

	def getRootNode( self ):
		return self

	def getNodeParent( self, node ): # reimplemnt for target node	
		if node == self:
			return None
		return self

	def getNodeChildren( self, node ):
		if node == self:
			if self.target:
				return [ cv for cv in list(self.target.variables.values()) ]
			else:
				return []
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self: return
		vtype = node.vtype
		item.setText( 0, node.name )
		item.setText( 2, node.desc )
		if vtype == 'boolean':
			item.setIcon( 0, getIcon( 'var_boolean' ) )
			item.setText( 1, node.value and 'true' or 'false' )
		elif vtype == 'number':
			item.setIcon( 0, getIcon( 'var_number' ) )
			item.setText( 1, '%.4f' % node.value )
		elif vtype == 'int':
			item.setIcon( 0, getIcon( 'var_int' ) )
			item.setText( 1, '%d' % node.value )
		elif vtype == 'string':
			item.setIcon( 0, getIcon( 'var_string' ) )
			item.setText( 1, node.value )

	def onItemChanged( self, item, col ):
		node = self.getNodeByItem( item )
		if col == 0:
			node.name = item.text( 0 )
		elif col == 1:
			node.set( node, item.text( 1 ) )
		elif col == 2:
			node.desc = item.text( 2 )
		self.refreshNode( node )

##----------------------------------------------------------------##
class ControlVariableEditorWidget( QtWidgets.QWidget ):
	def __init__( self, *args, **kwargs ):
		super( ControlVariableEditorWidget, self ).__init__( *args, **kwargs )

		self.target = None

		layout = QtWidgets.QVBoxLayout( self )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 1 , 1 , 1 , 1 )
		self.tree = ControlVariableSetTreeWidget( self )
		self.tree.setSizePolicy(
				QtWidgets.QSizePolicy.Expanding,
				QtWidgets.QSizePolicy.Expanding
				)
		self.filter = GenericTreeFilter( self )
		self.filter.setTargetTree( self.tree )
		self.toolbar = QtWidgets.QToolBar( self )
		self.toolbar.setIconSize( QtCore.QSize( 16, 16 ) )
		self.actionAddI = self.toolbar.addAction( getIcon( 'var_int' ), 'Add Int' )
		self.actionAddB = self.toolbar.addAction( getIcon( 'var_boolean' ), 'Add Boolean' )
		self.actionAddN = self.toolbar.addAction( getIcon( 'var_number' ), 'Add Number' )
		self.actionAddS = self.toolbar.addAction( getIcon( 'var_string' ), 'Add String' )
		self.actionRemove = self.toolbar.addAction( getIcon( 'remove' ), 'Remove' )
		self.toolbar.addSeparator()
		self.actionRefresh = self.toolbar.addAction( getIcon( 'refresh' ), 'Refresh' )
		layout.addWidget( self.toolbar )
		layout.addWidget( self.filter )
		layout.addWidget( self.tree )

		self.actionAddI    .triggered .connect( self.onActionAddI    )
		self.actionAddN    .triggered .connect( self.onActionAddN    )
		self.actionAddB    .triggered .connect( self.onActionAddB    )
		self.actionAddS    .triggered .connect( self.onActionAddS    )
		self.actionRemove  .triggered .connect( self.onActionRemove  )
		self.actionRefresh .triggered .connect( self.onActionRefresh )

	def refresh( self ):
		self.tree.rebuild()

	def setTarget( self, target ):
		self.target = target
		self.tree.setTarget( target )
		self.toolbar.setEnabled( target and True or False )

	def onActionAddI( self ):
		self.onActionAdd( 'int' )

	def onActionAddB( self ):
		self.onActionAdd( 'boolean' )

	def onActionAddN( self ):
		self.onActionAdd( 'number' )

	def onActionAddS( self ):
		self.onActionAdd( 'string' )

	def onActionAdd( self, vtype ):
		if not self.target: return
		target = self.target
		newVar = target.addVar( target, 'Var', vtype )
		self.tree.addNode( newVar )
		self.tree.editNode( newVar )
		self.tree.selectNode( newVar )

	def onActionRemove( self ):
		if not self.target: return
		selection = self.tree.getSelection()
		for var in selection:
			self.target.removeVar( self.target, var ) #lua
			self.tree.removeNode( var )

	def onActionRefresh( self ):
		if not self.target: return
		self.tree.refreshAllContent()

##----------------------------------------------------------------##
class ControlVariableSetEditor( ObjectEditor ): #a generic property grid 
	def initWidget( self, container, objectContainer ):
		self.widget = ControlVariableEditorWidget( container )
		return self.widget

	def setTarget( self, target ):
		self.target = target
		self.widget.setTarget( target )

	def refresh( self ):
		self.widget.refresh()

	def unload( self ):
		self.target = None
		self.widget.setTarget( None )

##----------------------------------------------------------------##
@slot( 'module.loaded' )
def registerControlVariableSetEditor():
	registerObjectEditor( _MOCK.ControlVariableSet, ControlVariableSetEditor )


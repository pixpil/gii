import logging

from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtWidgets import QMenu, QMenuBar, QToolBar, QAction

from gii.core import signals, app
from .Menu import MenuManager
from gii.qt.IconCache import getIcon

class ToolBarItem(object):
	def __init__( self, name, **option ):
		option = option or {}
		self.name     = name.lower()
		self.label    = option.get( 'label', name )	
		self.priority = option.get( 'priority', 0 )
		self.shortcut = option.get( 'shortcut', False )
		self.cmd      = option.get( 'command', None )
		self.cmdArgs  = option.get( 'command_args', None )
		self.groupId  = option.get( 'group', None )
		iconName      = option.get( 'icon', None )
		self.icon     = iconName and getIcon( iconName ) or None

		self.parent  = None
		self.owner   = None
		
		self.onClick = None
		self.signal  = None
		self.itemType = False

		widget   = option.get( 'widget', None )
		menuLink = option.get( 'menu_link')

		if widget:
			self.qtAction   = QtWidgets.QWidgetAction( None )
			self.qtAction.setDefaultWidget( widget )

		elif menuLink:
			m = MenuManager.get().find( menuLink )
			if m and hasattr( m, 'qtAction' ):
				self.qtAction = m.qtAction
			else:
				logging.error( 'not valid menu link:' + self.menuLink )
				self.qtAction = QtWidgets.QAction( self.label, None )					

		else:
			self.itemType = option.get( 'type', False )
			self.onClick  = option.get( 'on_click', None )
			self.signal   = None
			self.qtAction   = QtWidgets.QAction( 
				self.label, None,
				checkable = self.itemType == 'check',
				triggered = self.handleEvent,
				shortcut  = self.shortcut
				)

		if self.icon:
			self.qtAction.setIcon( self.icon )

	def setEnabled( self, enabled = True ):
		self.qtAction.setEnabled( enabled )

	def getName( self ):
		return self.name

	def getAction( self ):
		return self.qtAction

	def getValue(self):
		if self.itemType in ('check','radio'):
			return self.qtAction.isChecked()
		return True

	def setValue( self, value ):
		if self.itemType in ('check','radio'):
			self.qtAction.setChecked( value and True or False )

	def getOwner( self ):
		if self.owner: return self.owner
		if self.parent: return self.parent.getOwner()
		return None

	def handleEvent( self ):
		value = self.getValue()
		owner = self.getOwner()
		if owner and hasattr( owner, 'onTool' ):
			owner.onTool( self )
		if self.signal:
			self.signal( value )
		if self.onClick != None:
			self.onClick( value )
		if self.cmd:
			args = self.cmdArgs or {}
			app.doCommand( self.cmd, **args )
	
	def trigger( self ):
		if self.qtAction:
			self.qtAction.trigger()

		
class ToolBarNode(object):
	"""docstring for ToolBar"""
	def __init__(self, name, qtToolbar, **option):
		self.name = name or ''
		assert isinstance( qtToolbar, QToolBar )
		self.qtToolbar = qtToolbar
		self.items     = {}
		self.groups    = {}
		self.owner     = option.get( 'owner', None )
		label = option.get( 'label', name )
		qtToolbar.setWindowTitle( label )
		qtToolbar.setObjectName( name )
		if not hasattr( qtToolbar, '_icon_size' ):
			iconSize = option.get( 'icon_size', 16 )
			qtToolbar.setIconSize( QtCore.QSize( iconSize, iconSize ) )

	def getQtToolbar( self ):
		return self.qtToolbar

	def affirmGroup( self, id ):
		group = self.groups.get( id, None )
		if not group:
			group = QtWidgets.QActionGroup( self.qtToolbar )
			self.groups[ id ] = group
		return group

	def addTools( self, dataList ):
		for data in dataList:
			if data == '----':
				self.addTool( data )
			elif isinstance( data, dict ):
				name = data.get( 'name', None )
				if name:
					self.addTool( **data )

	def addTool( self, name, **option ):
		if name == '----':
			self.qtToolbar.addSeparator()
			return
		item = ToolBarItem( name, **option )
		self.items[ name ] = item
		self.qtToolbar.addAction( item.qtAction )
		item.parent = self
		
		if item.groupId:
			group = self.affirmGroup( item.groupId )
			group.addAction( item.qtAction )

		return item

	def addWidget( self, widget ):
		return self.qtToolbar.addWidget( widget )

	def getQtToolBar( self ):
		return self.qtToolbar

	def addSeparator( self ):
		self.qtToolbar.addSeparator()

	def getTool( self, name ):
		return self.items.get( name, None )

	def removeTool( self, name ):
		tool = self.getTool( name )
		if tool:
			self.qtToolbar.removeAction( tool.qtAction )
			del self.items[ name ]

	def enableTool( self, name, enabled = True ):
		tool = self.getTool( name )
		if tool:
			tool.setEnabled( enabled )

	def setEnabled( self, enabled = True ):
		self.qtToolbar.setEnabled( enabled )

	def setValue( self, value ):
		pass

	def setVisible( self, vis = True ):
		self.qtToolbar.setVisible( vis )

	def hide( self ):
		self.setVisible( False )

	def show( self ):
		self.setVisible( True )

	def getOwner( self ):
		return self.owner



class ToolBarManager(object):
	"""docstring for ToolBarManager"""
	_singleton = None
	@staticmethod
	def get():
		return ToolBarManager._singleton

	def __init__(self):
		assert not ToolBarManager._singleton
		ToolBarManager._singleton = self
		self.toolbars = {}

	def addToolBar( self, name, toolbar, owner, **option ):
		tb = ToolBarNode( name, toolbar, **option )
		tb.owner = owner
		if name:
			self.toolbars[ name ] = tb
		return tb

	def find( self, path ):
		blobs = path.split('/')
		l = len(blobs)
		if l< 1 or l > 2: 
			logging.error( 'invalid toolbar path' + path )
			return None

		toolbar = self.toolbars.get( blobs[0] )
		if l == 2 :
			return toolbar and toolbar.getTool( blobs[1] ) or None
		return toolbar 

	def addTool( self, path, option = {}, owner = None ):
		blobs = path.split('/')
		if len(blobs) != 2:
			logging.error( 'invalid toolbar item path' + path )
			return None

		toolbar = self.find( blobs[0] )
		if toolbar:
			tool = toolbar.addTool( blobs[1], **option )
			if tool: tool.owner = owner
			return tool
		logging.error( 'toolbar not found:' + blobs[0] )
		return None

	def enableTool( self, path, enabled = True ):
		tool = self.find( path )
		if tool:
			tool.setEnabled( enabled )
		else:
			logging.error( 'toolbar/tool not found:' + path )


def wrapToolBar( name, qtToolbar, **kwargs ):
	barnode = ToolBarNode( name, qtToolbar, **kwargs )
	return barnode

ToolBarManager()
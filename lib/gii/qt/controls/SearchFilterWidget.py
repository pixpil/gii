import sys
import math
from gii.qt.controls.FlowLayout import FlowLayout
from gii.qt.controls.ElidedLabel import ElidedLabel
from gii.qt.IconCache               import getIcon
from gii.qt.helpers    import addWidgetWithLayout, restrainWidgetToScreen

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtGui import QColor, QTransform, qRgb
from qtpy.QtWidgets import QStyle

from util.SearchFilter import *

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

SearchFilterEdit,BaseClass = uic.loadUiType( _getModulePath('SearchFilterEdit.ui') )

##----------------------------------------------------------------##
class SearchFilterEditWindow( QtWidgets.QFrame ):
	changed   = Signal()
	cancelled = Signal()
	def __init__( self, *args ):
		super( SearchFilterEditWindow, self ).__init__( *args )
		self.ui = SearchFilterEdit()
		self.ui.setupUi( self )
		self.setWindowFlags( Qt.Popup )
		self.installEventFilter( self )

		self.ui.buttonCancel.clicked.connect( self.onButtonCancel )
		self.ui.buttonOK.clicked.connect( self.onButtonOK )
		self.ui.lineEditCiteria.installEventFilter( self )
		self.ui.lineEditAlias.installEventFilter( self )

		self.targetItem = None
		self.editSubmitted = False

	def eventFilter(self, obj, event):
		e = event.type()
		if e == QEvent.WindowDeactivate:
			self.close()
		elif e == QEvent.KeyPress:
			if event.key() in ( Qt.Key_Enter, Qt.Key_Return ) and ( event.modifiers() & Qt.ControlModifier ):
				self.onButtonOK()
				return True

		return False

	def setTargetItem( self, item ):
		self.targetItem = item
		self.editSubmitted = False
		self.ui.lineEditAlias.setText( item.getAlias() )
		self.ui.lineEditCiteria.setText( item.getCiteria() )
		self.ui.checkLocked.setCheckState( item.isLocked() and Qt.Checked or Qt.Unchecked )

	def _submit( self ):
		if not self.targetItem: return
		#update item
		locked  = self.ui.checkLocked.checkState() == Qt.Checked
		alias   = self.ui.lineEditAlias.text()
		citeria = self.ui.lineEditCiteria.text()
		self.targetItem.setLocked( locked )
		self.targetItem.setAlias( alias )
		self.targetItem.setCiteria( citeria )
		self.changed.emit()

	def closeEvent( self, ev ):
		super( SearchFilterEditWindow, self ).closeEvent( ev )
		if self.editSubmitted:
			self._submit()
		else:
			self.cancelled.emit()
		self.editSubmitted = False

	def onButtonCancel( self ):
		self.editSubmitted = False
		self.close()

	def onButtonOK( self ):
		self.editSubmitted = True
		self.close()



##----------------------------------------------------------------##
class SearchFilterItemWidget( QtWidgets.QToolButton ):
	def __init__( self, *args, **kwargs ):
		super( SearchFilterItemWidget, self ).__init__( *args, **kwargs )
		self.setCheckable( True )
		self.setText( '' )
		self.setFixedHeight( 20 )
		self.setFocusPolicy( Qt.NoFocus )
		self.setCursor( Qt.PointingHandCursor )
		self.setMouseTracking( True )
		self.locked = False
		self.targetItem = None

		self.installEventFilter( self )
		self.clicked.connect( self.onClicked )

	def setTargetItem( self, item ):
		self.targetItem = item
		self.refresh()

	def refresh( self ):
		item = self.targetItem
		self.setText( item.toString() )
		self.setLocked( item.isLocked() )
		self.setChecked( item.isActive() )

	def setLocked( self, locked ):
		self.locked = locked
		if locked:
			self.setChecked( True )
		self.setProperty( 'locked', locked )
		self.setEnabled( not locked )

	def eventFilter( self, obj, ev ):
		e = ev.type()
		if e == QtCore.QEvent.MouseButtonPress:
			if ev.button() == Qt.RightButton:
				parent = self.parent()
				if parent: parent.popItemContextMenu( self )
		return False

	def onClicked( self ):
		self.targetItem.setActive( self.isChecked() )
		self.parent().onItemToggled( self )

##----------------------------------------------------------------##
class SearchFilterWidget( QtWidgets.QFrame ):
	filterChanged = Signal()
	def __init__( self, *args, **kwargs ):
		super( SearchFilterWidget, self ).__init__( *args, **kwargs )
		self.currentContextItem = None
		self.currentContextItemWidget = None
		self.currentNewItem = None
		
		self.editWindow = SearchFilterEditWindow( self )
		self.editWindow.hide()
		self.targetFilter = None

		self.setMinimumSize( 50, 20 )
		layout = FlowLayout( self )
		layout.setSpacing( 2 )
		layout.setContentsMargins( 5 , 5 , 5 , 5 )

		self.buttonAdd = QtWidgets.QToolButton( self )
		self.buttonAdd.setFixedHeight( 20 )
		self.buttonAdd.setIcon( getIcon( 'filter' ) )
		self.buttonAdd.setFocusPolicy( Qt.NoFocus )
		self.buttonAdd.clicked.connect( self.onActionAdd )
		layout.addWidget( self.buttonAdd )

		self.itemToWidget = {}

		self.itemContextMenu = menu = QtWidgets.QMenu( 'Filter Item Context' )
		menu.addAction( 'Filter' ).setEnabled( False )
		menu.addSeparator()

		# actionAdd = menu.addAction( 'Add' )
		# menu.addSeparator()
		actionLock = menu.addAction( 'Lock/Unlock' )
		actionEdit = menu.addAction( 'Edit' )
		menu.addSeparator()
		actionDelete = menu.addAction( 'Delete' )
		# actionAdd    .triggered .connect( self.onActionAdd )
		actionLock   .triggered .connect( self.onActionLock )
		actionEdit   .triggered .connect( self.onActionEdit )
		actionDelete .triggered .connect( self.onActionDelete )
		self.editWindow.changed.connect( self.onEditChanged )
		self.editWindow.cancelled.connect( self.onEditCancelled )

	def setTargetFilter( self, targetFilter ):
		self.targetFilter = targetFilter
		self.rebuild()
		self.notifyFilterChange()

	def _clear( self ):
		layout = self.layout()
		while layout.takeAt( 1 ):
			pass
		for item, widget in list(self.itemToWidget.items()):
			widget.setParent( None )
			widget.deleteLater()
		self.itemToWidget = {}

	def rebuild( self ):
		self.hide()
		self._clear()
		if not self.targetFilter: return
		items = self.targetFilter.getItems()
		#sort
		for item in items:
			if item.isLocked():
				self._addItem( item )	

		for item in items:
			if not item.isLocked():
				self._addItem( item )	
		self.show()

	def _removeItem( self, item ):
		widget = self.itemToWidget.get( item, None )
		if not widget: return
		del self.itemToWidget[ item ]
		widget.targetItem = None

	def _addItem( self, item ):
		itemWidget = SearchFilterItemWidget( self )
		itemWidget.setTargetItem( item )
		self.layout().addWidget( itemWidget )
		self.itemToWidget[ item ] = itemWidget

	def startEditItem( self, item ):
		self.editWindow.setTargetItem( item )
		self.editWindow.move( QtGui.QCursor.pos() )
		restrainWidgetToScreen( self.editWindow )
		self.editWindow.show()
		self.editWindow.raise_()
		self.editWindow.ui.lineEditCiteria.setFocus()

	def onActionAdd( self ):
		self.currentContextItem = None
		self.currentNewItem = SearchFilterItem()
		self.startEditItem( self.currentNewItem )

	def onActionLock( self ):
		item = self.currentContextItem
		item.setLocked( not item.isLocked() )
		self.itemToWidget[ item ].setLocked( item.isLocked() )
		self.rebuild()
		self.currentContextItem = None

	def onActionEdit( self ):
		self.currentNewItem = None
		self.startEditItem( self.currentContextItem )
		self.currentContextItem = None

	def onActionDelete( self ):
		self.targetFilter.removeItem( self.currentContextItem )
		self.rebuild()
		self.currentContextItem = None
		self.targetFilter.markDirty()
		self.notifyFilterChange()

	def onEditChanged( self ):
		editItem = self.editWindow.targetItem
		if self.currentNewItem == editItem:
			self.targetFilter.addItem( self.currentNewItem )
			self.currentNewItem = None
			self.rebuild()
		else:
			self.currentContextItemWidget.refresh()
		self.targetFilter.markDirty()
		self.notifyFilterChange()

	def onEditCancelled( self ):
		self.rebuild()

	def onItemToggled( self, itemWidget ):
		self.targetFilter.markDirty()
		self.notifyFilterChange()

	def popItemContextMenu( self, itemWidget ):
		self.currentContextItemWidget = itemWidget
		self.currentContextItem = itemWidget.targetItem
		self.itemContextMenu.exec_( QtGui.QCursor.pos() )

	def getCurrentContextItem( self ):
		return self.currentContextItem

	def notifyFilterChange( self ):
		self.filterChanged.emit()

######TEST
if __name__ == '__main__':
	import sys
	app = QtWidgets.QApplication( sys.argv )
	styleSheetName = 'gii.qss'
	app.setStyleSheet(
			open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
		)

	filter = SearchFilter()
	item   = SearchFilterItem()
	item.setAlias( 'Alias' )
	item.setCiteria( 't:test' )
	# item.setLocked( True )
	filter.addItem( item )
	widget = SearchFilterWidget()
	widget.show()
	widget.setTargetFilter( filter )
	widget.raise_()

	app.exec_()


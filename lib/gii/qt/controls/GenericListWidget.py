from qtpy import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore import Qt, QSize, Signal
from qtpy.QtWidgets import QApplication

from gii.qt.IconCache import getIcon
from gii.qt.helpers import repolishWidget
import re, fnmatch

##----------------------------------------------------------------##
class no_editItemDelegate( QtWidgets.QStyledItemDelegate ):
	def createEditor( *args ):
		return None


##----------------------------------------------------------------##
class GenericListWidget( QtWidgets.QListWidget ):
	def __init__( self, *args, **option ):
		super( GenericListWidget, self ).__init__( *args )
		
		self.nodeDict = {}
		self.refreshing = False
		self.option = option

		if option.get( 'mode', 'list' ) == 'icon':
			self.setViewMode( QtWidgets.QListView.IconMode )
			
		self.itemDoubleClicked    .connect( self.onDClicked )
		self.itemClicked          .connect( self.onClicked )
		self.itemSelectionChanged .connect( self.onItemSelectionChanged )
		self.itemActivated        .connect( self.onItemActivated )
		self.itemChanged          .connect( self._onItemChanged )

		self.setHorizontalScrollMode( QtWidgets.QAbstractItemView.ScrollPerPixel )
		self.setVerticalScrollMode( QtWidgets.QAbstractItemView.ScrollPerPixel )

		if self.getOption( 'multiple_selection', False ):
			self.setSelectionMode( QtWidgets.QAbstractItemView.ExtendedSelection )
		else:
			self.setSelectionMode( QtWidgets.QAbstractItemView.SingleSelection )

		self.setSortingEnabled( self.getOption('sorting', True) )

		dragMode = self.getOption( 'drag_mode', None )
		if dragMode == 'all':
			self.setDragDropMode( QtWidgets.QAbstractItemView.DragDrop )
		elif dragMode == 'drag':
			self.setDragDropMode( QtWidgets.QAbstractItemView.DragOnly )
		elif dragMode == 'drop':
			self.setDragDropMode( QtWidgets.QAbstractItemView.DropOnly )
		elif dragMode == 'internal' or dragMode == True:
			self.setDragDropMode( QtWidgets.QAbstractItemView.InternalMove )
			

	def getOption( self, k, v ):
		defOption = self.getDefaultOptions()
		option    = self.option
		if defOption:
			defValue = defOption.get( k, v )
		else:
			defValue = v
		return option.get( k, defValue )


	def rebuild( self ):
		self.setUpdatesEnabled( False )
		self.clear()
		self.nodeDict = {}
		nodes = self.getNodes()
		for node in nodes:
			self.addNode( node )
		self.setUpdatesEnabled( True )

	def getItemByNode( self, node ):
		return self.nodeDict.get( node, None )

	def getNodeByItem( self, item ):
		if hasattr( item, 'node' ):
			return item.node
		return None

	def refreshNode(self, node):
		item = self.getItemByNode( node )
		if item:
			if item == self.rootItem:
				self.rebuild()
				return
			self.removeNode( node )
			self.addNode( node )

	def refreshAllContent( self ):
		for node in self.nodeDict.keys():
			self.refreshNodeContent( node )

	def refreshNodeContent( self, node, **option ):
		prevRefreshing = self.refreshing
		self.refreshing = True
		item=self.getItemByNode( node )
		if item:
			self.updateItemContent( item, node, **option )
		self.refreshing = prevRefreshing

	def refreshAllContent( self ):
		for node in self.nodeDict.keys():
			self.refreshNodeContent( node )

	def hasNode( self, node ):
		return self.getItemByNode( node ) != None

	def addNode( self, node, **option ):
		assert not node is None, 'attempt to insert null node '
		item = self.nodeDict.get( node, None )
		if item: return item
		item = QtWidgets.QListWidgetItem( self )
		self.nodeDict[ node ] = item
		item.node = node
		self.updateItem( node )
		return item

	def _removeItem( self, item ):
		node = item.node
		item.node = None
		del self.nodeDict[ node ]
		row = self.row( item )
		self.takeItem( row )
		return True

	def removeNode( self, node ):
		item = self.nodeDict.get( node, None )
		if not item: return
		self._removeItem( item )


	def getItemFlags( self, node ):
		return {}

	def _calcItemFlags( self, node ):
		flags = Qt.ItemIsEnabled 
		flagNames = self.getItemFlags( node )
		if flagNames.get( 'selectable', True ): flags |= Qt.ItemIsSelectable
		if flagNames.get( 'draggable',  True ): flags |= Qt.ItemIsDragEnabled
		if flagNames.get( 'droppable',  True ): flags |= Qt.ItemIsDropEnabled
		if self.getOption( 'editable', False ):
			if flagNames.get( 'editable',   True ): flags |= Qt.ItemIsEditable
		return flags

	def updateItem( self, node, **option ):
		item = self.getItemByNode(node)
		if not item: return False
		self.refreshing = True
		self.updateItemContent( item, node, **option )
		flags = self._calcItemFlags( node )
		item.setFlags( flags )
		self.refreshing = False

	def selectNode( self, node, **kwargs ):
		if not kwargs.get( 'add', False ):
				self.selectionModel().clearSelection()
		if not node: return
		if isinstance( node, (tuple, list) ):
			for n in node:
				item = self.getItemByNode( n )
				if item:
					item.setSelected( True )
			if kwargs.get('goto',True) : 
				first = len( node ) > 0 and node[0]
				if first:
					self.gotoNode( first )
		else:
			item = self.getItemByNode( node )
			if item:
				item.setSelected( True )
				if kwargs.get('goto',True) : 
					self.gotoNode( node )

	def getSelection( self ):
		return [ item.node for item in self.selectedItems() ]

	def getFirstSelection( self ):
		for item in self.selectedItems():
			return item.node
		return None

	def setFocusedItem(self, item ):
		idx = self.indexFromItem( item )
		if idx:
			self.setCurrentIndex( idx )

	def editNode( self, node ):
		item = self.getItemByNode( node )
		if item:
			self.editItem( item )

	def scrollToNode( self, node ):
		item = self.getItemByNode( node )
		if item:
			self.scrollToItem( item )

	def gotoNode( self, node ):
		item = self.getItemByNode( node )
		if item:
			self.scrollToItem( item )
			self.setCurrentItem( item, QtCore.QItemSelectionModel.Current )
			# self.moveCursor( self.MoveUp, Qt.NoModifier )

	##----------------------------------------------------------------##
	#custom control
	def keyPressEvent( self, ev ):
		modifiers = QApplication.keyboardModifiers()
		key = ev.key()

		if key in ( Qt.Key_Delete, Qt.Key_Backspace ):			
			self.onDeletePressed()
		elif key == Qt.Key_Escape: #deselect all
			self.selectNode( [] )

		#copy&paste
		elif ( key, modifiers ) == ( Qt.Key_C, Qt.ControlModifier ):
			if self.onClipboardCopy(): return
		elif ( key, modifiers ) == ( Qt.Key_X, Qt.ControlModifier ):
			if self.onClipboardCut(): return
		elif ( key, modifiers ) == ( Qt.Key_V, Qt.ControlModifier ):
			if self.onClipboardPaste(): return

		#open
		elif key == Qt.Key_Down \
			and ( modifiers in ( Qt.ControlModifier, Qt.ControlModifier | Qt.KeypadModifier ) ):
			item = self.currentItem() 
			if item:
				self.onItemActivated( item )
				return

		return super( GenericListWidget, self ).keyPressEvent( ev )

	def mousePressEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			item = self.itemAt( ev.pos() )
			if not item and ev.modifiers() != Qt.NoModifier: #root
				self.clearSelection()
				return 
		return super( GenericListWidget, self ).mousePressEvent( ev )

	# def updateGeometries( self ):
	# 	super( GenericListWidget, self ).updateGeometries()
	# 	step = self.verticalScrollBar().singleStep()/5.0
	# 	print( 'vertical step', step )
	# 	self.verticalScrollBar().setSingleStep( step )
	
	##----------------------------------------------------------------##
	##Virtual
	##----------------------------------------------------------------##
	def getDefaultOptions( self ):
		return None

	def getNodes( self ):
		return []		

	def updateItemContent( self, item, node, **option ):
		pass


	##----------------------------------------------------------------##
	# Event Callback
	##----------------------------------------------------------------##
	def onClicked(self, item ):
		pass

	def onDClicked(self, item ):
		pass
		
	def onItemSelectionChanged(self):
		pass

	def onItemActivated(self, item):
		pass

	def onClipboardCopy( self ):
		pass

	def onClipboardCut( self ):
		pass

	def onClipboardPaste( self ):
		pass

	def _onItemChanged( self, item ):
		if self.refreshing: return
		return self.onItemChanged( item )

	def onItemChanged( self, item ):
		pass

	def onDeletePressed( self ):
		pass


##----------------------------------------------------------------##	
class GenericListFilter( QtWidgets.QWidget ):
	filterChanged = Signal( str )
	def __init__(self, *args ):
		super(GenericListFilter, self).__init__( *args )
		
		self.targetList = None

		self.setSizePolicy( 
			QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
		)
		self.setMinimumSize( 100, 20 )
		layout = QtWidgets.QHBoxLayout( self )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		layout.setSpacing( 0 )
		
		self.buttonClear = QtWidgets.QToolButton( self )
		self.buttonClear.setText( 'X' )
		self.buttonClear.setObjectName( 'ClearButton' )
		self.buttonClear.setIconSize( QtCore.QSize( 12, 12 ) )
		self.buttonClear.setIcon( getIcon('remove') )
		self.lineEdit = QtWidgets.QLineEdit( self )
		self.lineEdit.textChanged.connect( self.onTextChanged )
		self.lineEdit.setPlaceholderText( 'Filters' )

		self.lineEdit.setMinimumSize( 100, 20 )
		self.lineEdit.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
		self.lineEdit.installEventFilter( self )
		self.buttonClear.hide()

		layout.addWidget( self.buttonClear )
		layout.addWidget( self.lineEdit )

		self.buttonClear.clicked.connect( self.clearFilter )

	def eventFilter( self, object, event ):
		e=event.type()
		if e == QtCore.QEvent.KeyPress:
			key = event.key()
			if key == Qt.Key_Escape:
				self.clearFilter()
				return True
			elif key in [ Qt.Key_Down, Qt.Key_PageDown, Qt.Key_PageUp ]:
				self.targetList.setFocus()
				return True
		return False

	def setTargetList( self, tree ):
		self.targetList = tree

	def onTextChanged( self, text ):
		self.applyFilter( text )
		self.filterChanged.emit( text )

	def refresh( self ):
		self.applyFilter( self.getFilter() )

	def applyFilter( self, pattern ):
		if not self.targetList: return
		if not self.isEnabled(): return
		pattern = pattern.strip()
		if pattern:
			regex = '.*'.join( map(re.escape, pattern.upper()) )
			ro = re.compile( regex )
		else:
			ro = None
		if ro:
			self.targetList.setProperty( 'filtered', True )
			self.buttonClear.show()
		else:
			self.targetList.setProperty( 'filtered', False )
			self.buttonClear.hide()
		self.targetList.hide()
		for item in self.targetList.nodeDict.values():
			self.applyFilterToItem( item, ro )
		repolishWidget( self.targetList )
		self.targetList.show()
		self.targetList.verticalScrollBar().setValue( 0 )

	def applyFilterToItem( self, item, ro ):
		if not ro:
			item.setHidden( False )
			return 
			
		value = item.text().upper()
		if ro.search( value ):
			item.setHidden( False )
		else:
			item.setHidden( True )

	def setFilter( self, text ):
		self.lineEdit.setText( text )

	def getFilter( self ):
		return self.lineEdit.text()

	def clearFilter( self ):
		self.lineEdit.setText( '' )

	
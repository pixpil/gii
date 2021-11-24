import re, fnmatch
import sip

from qtpy import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore import Qt, QSize, Signal
from qtpy.QtGui import QBrush, QColor, QPen, QIcon
from qtpy.QtWidgets import QApplication, QStyle

from gii.qt.helpers import repolishWidget
from gii.qt.IconCache import getIcon

##----------------------------------------------------------------##
class ReadonlyItemDelegate( QtWidgets.QStyledItemDelegate ):
	def createEditor( *args ):
		return None

##----------------------------------------------------------------##
class DragSession():
	def __init__( self, tree ):
		self.target = None
		self.tree = tree
		self.timer = QtCore.QTimer( tree )
		self.timer.setSingleShot( True )
		self.timer.setInterval( 700 )
		self.timer.timeout.connect( self.onTimeout )

	def setTarget( self, item ):
		if self.target == item: return
		self.target = item
		if item:
			self.timer.start()
		else:
			self.timer.stop()

	def onTimeout( self ):
		if self.target and ( not sip.isdeleted( self.target ) ):
			if self.target.isExpanded(): return
			self.target.setExpanded( True )

	def stop( self ):
		self.timer.stop()


##----------------------------------------------------------------##
class GenericTreeWidget( QtWidgets.QTreeWidget ):
	def __init__( self, *args, **option ):
		super(GenericTreeWidget, self).__init__(*args)
		# self.setAttribute( Qt.WA_OpaquePaintEvent, True )
		# self.setAttribute(Qt.WA_MacShowFocusRect, False)
		self.setUniformRowHeights( True )
		self.setHorizontalScrollMode( QtWidgets.QAbstractItemView.ScrollPerPixel )
		self.setVerticalScrollMode( QtWidgets.QAbstractItemView.ScrollPerItem )
		self.nodeDict = {}
		
		self.readonlyItemDelegate = self.getReadonlyItemDelegate()
		self.defaultItemDelegate  = self.getDefaultItemDelegate()

		self.refreshing = False
		self.rebuilding = False
		self.firstSetup = True
		
		self.option = option
		headerInfo = self.getHeaderInfo()
		headerItem = QtWidgets.QTreeWidgetItem()
		self.setHeaderItem(headerItem)
		self.setItemDelegate( self.defaultItemDelegate )
		self.resetHeader()
	
		self.setSortingEnabled( self.getOption('sorting', True) )
	
		if self.getOption( 'multiple_selection', False ):
			self.setSelectionMode( QtWidgets.QAbstractItemView.ExtendedSelection )
		else:
			self.setSelectionMode( QtWidgets.QAbstractItemView.SingleSelection )

		dragMode = self.getOption( 'drag_mode', None )
		if dragMode == 'all':
			self.setDragDropMode( QtWidgets.QAbstractItemView.DragDrop )
		elif dragMode == 'drag':
			self.setDragDropMode( QtWidgets.QAbstractItemView.DragOnly )
		elif dragMode == 'drop':
			self.setDragDropMode( QtWidgets.QAbstractItemView.DropOnly )
		elif dragMode == 'internal' or dragMode == True:
			self.setDragDropMode( QtWidgets.QAbstractItemView.InternalMove )
			
		self.setAlternatingRowColors( self.getOption('alternating_color', False) )
		self.setExpandsOnDoubleClick( False )
		self.sortByColumn( 0, Qt.AscendingOrder )

		self.itemDoubleClicked    .connect( self.onDClicked )
		self.itemClicked          .connect( self.onClicked )
		self.itemExpanded         .connect( self.onItemExpanded )
		self.itemCollapsed        .connect( self.onItemCollapsed )
		self.itemSelectionChanged .connect( self.onItemSelectionChanged )
		self.itemActivated        .connect( self.onItemActivated )
		self.itemChanged          .connect( self._onItemChanged )
		self.setIndentation( 12 )

		self.initRootItem()

		self.dragSession = False
		
		
	def getReadonlyItemDelegate( self ):
		return ReadonlyItemDelegate( self )

	def getDefaultItemDelegate( self ):
		return QtWidgets.QStyledItemDelegate( self )

	def getOption( self, k, v ):
		defOption = self.getDefaultOptions()
		option    = self.option
		if defOption:
			defValue = defOption.get( k, v )
		else:
			defValue = v
		return option.get( k, defValue )

	def getDefaultOptions( self ):
		return None
		
	def initRootItem( self ):
		if self.getOption( 'show_root', False ):
			self.rootItem = self.createItem( None )
			self.invisibleRootItem().addChild( self.rootItem )
		else:
			self.rootItem = self.invisibleRootItem()

	def clear( self ):
		self.setUpdatesEnabled( False )
		for item in self.nodeDict.values():
			item.node = None
		self.nodeDict = {}
		super( GenericTreeWidget, self ).clear()
		self.initRootItem()
		self.rootItem.node = None
		self.setUpdatesEnabled( True )

	def rebuild( self, **option ):
		# columnCount = len( self.getHeaderInfo() )
		# columnSizes = [ self.columnWidth( idx ) for idx in range( columnCount ) ]
		self.rebuilding = True
		self.setUpdatesEnabled( False )
		self.clear()
		rootNode = self.getRootNode()
		if rootNode:
			self.addNode( rootNode )
			self.loadTreeStates()
		self.setUpdatesEnabled( True )
		self.rebuilding = False
		
		#workaround: avoid unexpected column resizing
		# if self.firstSetup:
		# 	self.resetHeader()
		# 	self.firstSetup = False
		# for idx, size in enumerate( columnSizes ): 
		# 	self.setColumnWidth( idx, size )

	def addNode( self, node, addChildren = True, **option ):
		assert not node is None, 'attempt to insert null node '
		item = self.nodeDict.get( node, None )
		if item:
			# print 'node already inserted?'
			return item
		pnode = self.getNodeParent( node )
		assert pnode != node, 'parent is item itself'
		if not pnode :
			item = self.rootItem
			item.node = node
		else:
			pitem = self.getItemByNode( pnode )
			if not pitem:
				pitem = self.addNode( pnode, False )
			item  = self.createItem( node )
			item.node = node
			assert pitem, ( 'node not found in tree:%s' % repr(pnode) )
			#find best new item index
			if not self.isSortingEnabled():
				newindex = None
				for i in range( pitem.childCount() ):
					childItem = pitem.child( i )
					node1 = childItem.node
					if self.compareNodes( node, node1 ):
						newindex = i
						break
				if newindex:
					pitem.insertChild( i, item )
				else:
					pitem.addChild( item )
			else:
				pitem.addChild( item )

		self.nodeDict[ node ]=item

		item.setExpanded( self.getOption( 'expanded', True ) )
			
		# if pnode:
		self.updateItem( node )
		if addChildren:
			children = self.getNodeChildren( node )
			if children:
				for child in children:
					self.addNode( child, True, **option )
		return item


	def getItemByNode(self, node):
		return self.nodeDict.get( node, None )

	def getNodeByItem( self, item ):
		if hasattr( item, 'node' ):
			return item.node
		return None

	def hasNode( self, node ):
		return self.getItemByNode( node ) != None

	def setNodeExpanded( self, node, expanded = True ):
		item = self.getItemByNode( node )
		if not item: return False
		item.setExpanded( expanded )
		return True

	def setAllExpanded( self, expanded = True ):
		for item in self.nodeDict.values():
			item.setExpanded( expanded )

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
		item = self.getItemByNode( node )
		if item:
			self.updateItemContent( item, node, **option )
			if option.get('updateChildren', False):
				children = self.getNodeChildren( node )
				if children:
					for child in children:
						self.refreshNodeContent( child , **option )
		self.refreshing = prevRefreshing

	def updateItem(self, node, **option ):
		return self._updateItem( node, None, **option )

	def updateHeaderItem( self, item, col, info ):
		pass

	def resetHeader( self ):
		headerInfo = self.getHeaderInfo()
		headerItem = self.headerItem()
		for i in range( 0, len(headerInfo) ):			
			info =  headerInfo[i]
			l = len( info )
			title = info[ 0 ]
			width = l > 1 and info[ 1 ] or -1
			if l > 2:
				editable = info[ 2 ] and True or False
			else:
				editable = i == 0
			headerItem.setText ( i, title )
			if not editable:
				self.setItemDelegateForColumn( i, self.readonlyItemDelegate )
			self.updateHeaderItem( headerItem, i, info )
			if width > 0:
				self.setColumnWidth ( i, width )

	def setFocusedItem(self, item ):
		idx = self.indexFromItem( item )
		if idx:
			self.setCurrentIndex( idx )

	def _calcItemFlags( self, node ):
		flags = Qt.ItemIsEnabled 
		flagNames = self.getItemFlags( node )
		if flagNames.get( 'selectable', True ): flags |= Qt.ItemIsSelectable
		if flagNames.get( 'draggable',  True ): flags |= Qt.ItemIsDragEnabled
		if flagNames.get( 'droppable',  True ): flags |= Qt.ItemIsDropEnabled
		if self.getOption( 'editable', False ):
			if flagNames.get( 'editable',   True ): flags |= Qt.ItemIsEditable
		return flags
		
	def _updateItem(self, node, updateLog=None, **option):
		item = self.getItemByNode(node)
		if not item: return False
		if not updateLog: updateLog={} #for avoiding duplicated updates
		if node in updateLog: return False
		updateLog[node]=True

		self.refreshing = True
		self.updateItemContent( item, node, **option )
		flags = self._calcItemFlags( node )
		item.setFlags( flags )
		self.refreshing = False

		if option.get('updateChildren',False):
			children = self.getNodeChildren( node )
			if children:
				for child in children:
					self._updateItem(child, updateLog, **option)

		return True

	def _removeItem( self, item ):
		for child in item.takeChildren():
			self._removeItem( child )
		node = item.node
		item.node = None
		del self.nodeDict[ node ]
		( item.parent() or self.rootItem ).removeChild( item )
		return True

	def removeNode(self, node):		
		item = self.getItemByNode( node )
		if item and item!=self.rootItem:
			self._removeItem( item )
			return True
		return False

	# def _detachNode( self, node ): #dangerous method
	# 	item = self.getItemByNode( node )
	# 	if item and item != self.rootItem:
	# 		( item.parent() or self.rootItem ).removeChild( item )
	# 		item.detachedParent = True

	# def _attachNode( self, node ):
	# 	item = self.getItemByNode( node )
	# 	if item and item != self.rootItem:
	# 		( item.parent() or self.rootItem ).removeChild( item )
	# 		item.detached = False

	def selectNode( self, node, **kw ):
		if not kw.get( 'add', False ):
				self.selectionModel().clearSelection()
		if not node: return
		if isinstance( node, (tuple, list) ):
			for n in node:
				item = self.getItemByNode( n )
				if item:
					item.setSelected( True )
			if kw.get('goto',True) : 
				first = len( node ) > 0 and node[0]
				if first:
					self.gotoNode( first )
		else:
			item = self.getItemByNode( node )
			if item:
				item.setSelected( True )
				if kw.get('goto',True) : 
					self.gotoNode( node )

	def selectFirstItem( self ):
		# if not self.treeResult.getSelection():
		self.clearSelection()
		item = self.itemAt( 0, 0 )
		if item:
			item.setSelected( True )
			self.scrollToItem( item )

	def editNode( self, node, col = 0 ):
		item = self.getItemByNode( node )
		if item:
			self.editItem( item, col )

	def scrollToNode( self, node ):
		item = self.getItemByNode( node )
		if item:
			self.scrollToItem( item )

	def gotoNode( self, node, col = 0 ):
		item = self.getItemByNode( node )
		if item:
			self.scrollToItem( item )
			self.setCurrentItem( item, col, QtCore.QItemSelectionModel.Current )
			# self.moveCursor( self.MoveUp, Qt.NoModifier )

	def setNodeVisible( self, node, visible = True ):
		item = self.getItemByNode( node )
		if item:
			item.setHidden( not visible )

	def sortOrder( self ):
		headerView = self.header()
		return headerView.sortIndicatorOrder()
	
	def getSelection( self ):
		return [ item.node for item in self.selectedItems() ]

	def getFirstSelection( self ):
		for item in self.selectedItems():
			return item.node
		return None

	def foldAllItems( self ):
		for item in self.nodeDict.values():
			if item and item != self.rootItem:
				item.setExpanded( False )

	def expandAllItems( self ):
		for item in self.nodeDict.values():
			if item:
				item.setExpanded( True )

	def isNodeExpanded( self, node ):
		item = self.getItemByNode( node )
		if item:
			return item.isExpanded()

	def isNodeVisible( self, node, considerFold = True ):
		item = self.getItemByNode( node )
		if item:
			if item.isHidden(): return False
			if considerFold:
				p = item.parent()
				while p:
					if not p.isExpanded(): return False
					p = p.parent()
			return True

	def getNodeVisualRect( self, node ):
		item = self.getItemByNode( node )
		if item:
			return self.visualItemRect( item )
		else:
			return None

	##----------------------------------------------------------------##
	## VIRTUAL Functions
	##----------------------------------------------------------------##	
	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass

	def getRootNode( self ):
		return None

	def getNodeParent( self, node ): # reimplemnt for target node
		return None

	def getNodeChildren( self, node ):
		return []

	def getItemFlags( self, node ):
		return {}

	def createItem( self, node ):
		item  = QtWidgets.QTreeWidgetItem()
		return item

	def updateItemContent( self, item, node, **option ):
		pass

	def getHeaderInfo( self ):
		return [('Name',100), ('State',30)]

	def compareNodes( self, n1, n2 ):
		return False

	def dragMoveEvent( self, ev ):
		if not self.dragSession:
			self.dragSession = DragSession( self )
		targetItem = self.itemAt( ev.pos() )
		self.dragSession.setTarget( targetItem )
		return super( GenericTreeWidget, self ).dragMoveEvent( ev )

	def dropEvent( self, ev ):
		if self.dragSession:
			self.dragSession.stop()

		p = self.dropIndicatorPosition()
		pos = False
		if p == QtWidgets.QAbstractItemView.OnItem: #reparent
			pos = 'on'
		elif p == QtWidgets.QAbstractItemView.AboveItem:
			pos = 'above'
		elif p == QtWidgets.QAbstractItemView.BelowItem:
			pos = 'below'
		else:
			pos = 'viewport'
		targetItem = self.itemAt( ev.pos() )
		if self.onDropEvent( targetItem and targetItem.node, pos, ev ) != False:
			super( GenericTreeWidget, self ).dropEvent( ev )
		else:
			ev.setDropAction( Qt.IgnoreAction )

	def onDropEvent( self, targetNode, pos, ev ):
		return False
		
	##----------------------------------------------------------------##
	# fold state
	##----------------------------------------------------------------##
	def retainFoldState( self ):
		output = {}
		for node, item in self.nodeDict.items():
			if not item: continue
			expanded = item.isExpanded()
			output[ node ] = expanded
		return output

	def restoreFoldState( self, data, defaultFoldState = None ):
		for node, item in self.nodeDict.items():
			if not item: continue
			state = data.get( node, defaultFoldState )
			if state != None:
				item.setExpanded( state )

	##----------------------------------------------------------------##
	# Event Callback
	##----------------------------------------------------------------##
	def onClicked(self, item, col):
		pass

	def onDClicked(self, item, col):
		pass
		
	def onItemSelectionChanged(self):
		pass

	def onItemActivated(self, item, col):
		pass

	def onItemExpanded( self, item ):
		pass

	def onItemCollapsed( self, item ):
		pass

	def onClipboardCopy( self ):
		pass

	def onClipboardCut( self ):
		pass

	def onClipboardPaste( self ):
		pass

	def _onItemChanged( self, item, col ):
		if self.refreshing: return
		return self.onItemChanged( item, col )

	def onItemChanged( self, item, col ):
		pass

	def onDeletePressed( self ):
		pass

	##----------------------------------------------------------------##
	#custom control
	def keyPressEvent( self, ev ):
		modifiers = QApplication.keyboardModifiers()
		key = ev.key()
		if key in ( Qt.Key_Delete, Qt.Key_Backspace ):			
			self.onDeletePressed()
		elif key == Qt.Key_Left: #move to parent node
			item = self.currentItem() 
			if item and not item.isExpanded():
				pitem = item.parent()
				if pitem and not pitem.isHidden():
					self.setCurrentItem( pitem )
					return
		elif key == Qt.Key_Escape: #deselect all
			self.selectNode( [] )
		#copy&paste
		elif key == Qt.Key_C and modifiers & Qt.ControlModifier:
			if self.onClipboardCopy(): return
		elif key == Qt.Key_X and modifiers & Qt.ControlModifier:
			if self.onClipboardCut(): return
		elif key == Qt.Key_V and modifiers & Qt.ControlModifier:
			if self.onClipboardPaste(): return
		#open
		elif key == Qt.Key_Down \
			and ( modifiers in ( Qt.ControlModifier, Qt.ControlModifier | Qt.KeypadModifier ) ):
			item = self.currentItem() 
			if item:
				self.onItemActivated( item, 0 )
				return

		elif key == Qt.Key_Down:
			if not self.currentItem():
				top = self.topLevelItem( 0 )
				self.setCurrentItem( top )
			else:
				item_below = self.itemBelow(self.currentItem())
				if item_below:
					self.setCurrentItem( item_below )
			return

		elif key == Qt.Key_Up:
			if not self.currentItem():
				top = self.topLevelItem( 0 )
				self.setCurrentItem( top )
			item_below = self.itemAbove(self.currentItem())
			if item_below:
				self.setCurrentItem( item_below )
			return

		return super( GenericTreeWidget, self ).keyPressEvent( ev )

	def mouseReleaseEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			item = self.itemAt( ev.pos() )
			if item and item.childCount() > 0  and ev.modifiers() == Qt.NoModifier:
				rect = self.visualItemRect( item )
				diff = rect.x() - ev.pos().x()
				if diff >= 7 and diff < 20:
					item.setExpanded( not item.isExpanded() )
		return super( GenericTreeWidget, self ).mouseReleaseEvent( ev )

	def mousePressEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			item = self.itemAt( ev.pos() )
			if not item and ev.modifiers() != Qt.NoModifier: #root
				self.clearSelection()
				return
		return super( GenericTreeWidget, self ).mousePressEvent( ev )

	def showEvent( self, ev ):
		#workaround: avoid unexpected column resizing
		if self.firstSetup:
			self.resetHeader()
			self.firstSetup = False
		return super( GenericTreeWidget, self ).showEvent( ev )


##----------------------------------------------------------------##	
class GenericTreeFilter( QtWidgets.QWidget ):
	filterChanged = Signal( str )
	def __init__(self, *args ):
		super(GenericTreeFilter, self).__init__( *args )
		
		self.targetTree = None

		self.setSizePolicy( 
			QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
		)
		self.setMinimumSize( 100, 20 )
		layout = QtWidgets.QHBoxLayout( self )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		layout.setSpacing( 0 )
		
		self.buttonFoldAll   = QtWidgets.QToolButton( self )
		self.buttonFoldAll.setIconSize( QtCore.QSize( 12, 12 ) )
		self.buttonFoldAll.setIcon( getIcon('collapse') )

		self.buttonUnfoldAll = QtWidgets.QToolButton( self )
		self.buttonUnfoldAll.setIconSize( QtCore.QSize( 12, 12 ) )
		self.buttonUnfoldAll.setIcon( getIcon('expand') )

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
		layout.addWidget( self.buttonFoldAll )
		layout.addWidget( self.buttonUnfoldAll )

		self.buttonClear.clicked.connect( self.clearFilter )
		self.buttonFoldAll.clicked.connect( self.foldTargetTree )
		self.buttonUnfoldAll.clicked.connect( self.unfoldTargetTree )

	def setFoldButtonsVisible( self, visible = True ):
		self.buttonFoldAll.setVisible( visible )
		self.buttonUnfoldAll.setVisible( visible )

	def eventFilter( self, object, event ):
		e=event.type()
		if e == QtCore.QEvent.KeyPress:
			key = event.key()
			if key == Qt.Key_Escape:
				self.clearFilter()
				return True
			elif key in [ Qt.Key_Down, Qt.Key_PageDown, Qt.Key_PageUp ]:
				self.targetTree.setFocus()
				return True
		return False

	def setTargetTree( self, tree ):
		self.targetTree = tree

	def onTextChanged( self, text ):
		self.filterChanged.emit( text )
		self.refresh()

	def refresh( self ):
		self.applyFilter( self.getFilter() )

	def applyFilter( self, pattern ):
		if not self.targetTree: return
		if not self.isEnabled(): return
		pattern = pattern.strip()
		if pattern:
			regex = '.*'.join( map(re.escape, pattern.upper()) )
			ro = re.compile( regex )
		else:
			ro = None
		if ro:
			self.targetTree.setProperty( 'filtered', True )
			self.buttonClear.show()
		else:
			self.targetTree.setProperty( 'filtered', False )
			self.buttonClear.hide()
		treeVis = self.targetTree.isVisible()
		# self.targetTree.hide()
		self.targetTree.setUpdatesEnabled( False )
		self.applyFilterToItem( self.targetTree.invisibleRootItem(), ro )
		repolishWidget( self.targetTree )
		if treeVis:
			self.targetTree.setUpdatesEnabled( True )
		self.targetTree.verticalScrollBar().setValue( 0 )

	def applyFilterToItem( self, item, ro ):
		count = item.childCount()
		childVisible = False
		for idx in range( count ):
			childItem = item.child( idx )
			if self.applyFilterToItem( childItem, ro ):
				childVisible = True
		value = item.text( 0 ).upper()
		if ro:
			selfVisible = ro.search( value ) and True or False
		else:
			selfVisible = True

		if selfVisible:
			item.setHidden( False )
			return True
		elif childVisible:
			item.setHidden( False )
			return True
		else:
			item.setHidden( True )
			return False

	def setFilter( self, text ):
		self.lineEdit.setText( text )

	def getFilter( self ):
		return self.lineEdit.text()

	def clearFilter( self ):
		self.lineEdit.setText( '' )

	def foldTargetTree( self ):
		if not self.targetTree: return
		self.targetTree.foldAllItems()

	def unfoldTargetTree( self ):
		if not self.targetTree: return
		self.targetTree.expandAllItems()


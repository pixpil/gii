from functools import cmp_to_key

from gii.core import *
from gii.core.model import *

from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
from gii.qt.controls.SimpleTitleBar import SimpleTitleBar
from gii.qt.helpers    import addWidgetWithLayout, restrainWidgetToScreen
from gii.qt.IconCache  import getIcon

from qtpy import QtWidgets, QtGui, QtCore, uic
from qtpy.QtCore import Qt
from qtpy.QtCore import QEventLoop, QEvent, QObject

import re

from polyleven import ratio

_SEARCHVIEW_ITEM_LIMIT = 100

# import difflib
##----------------------------------------------------------------##
def getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

SearchViewForm,BaseClass = uic.loadUiType(getModulePath('SearchView.ui'))

##----------------------------------------------------------------##
def _sortMatchScore( e1, e2 ):
	diff = e2.matchScore - e1.matchScore
	if diff > 0 : return 1
	if diff < 0 : return -1
	if e2.name > e1.name: return 1
	if e2.name < e1.name: return -1
	return 0

def _keyFuncName( x ):
	return x.name

	
##----------------------------------------------------------------##
class SearchViewWidget( QtWidgets.QWidget ):
	def __init__(self, *args ):
		self.titleBar = None

		super( SearchViewWidget, self ).__init__( *args )
		self.searchState = None
		self.defaultSortMethod = 'name'

		self.setWindowFlags( Qt.Window | Qt.FramelessWindowHint )
		self.setWindowModality( Qt.ApplicationModal )

		self.ui = SearchViewForm()
		self.ui.setupUi( self )
		
		self.editor = None
		self.treeResult = addWidgetWithLayout( 
				SearchViewTree(
					self.ui.containerResultTree,
					multiple_selection = False,
					editable = False,
					sorting  = False
				) 
			)
		self.treeResult.hideColumn( 0 )
		self.textTerms = addWidgetWithLayout (
			SearchViewTextTerm(self.ui.containerTextTerm )
			)
		self.textTerms.browser = self
		self.textTerms.textEdited.connect( self.onTermsChanged )
		self.textTerms.returnPressed.connect( self.onTermsReturn )

		self.setFocusProxy( self.textTerms )

		self.treeResult.browser = self
		self.entries = None
		self.setMinimumSize( 800, 300  )
		self.setMaximumSize( 800, 600  )
		self.multipleSelection = False

		self.setInfo( None )
		self.ui.buttonOK     .clicked .connect( self.onButtonOK )
		self.ui.buttonCancel .clicked .connect( self.onButtonCancel )

		self.ui.buttonAll     .clicked .connect( self.onButtonAll )
		self.ui.buttonInverse .clicked .connect( self.onButtonInverse )
		self.ui.buttonNone    .clicked .connect( self.onButtonNone )

		self.titleBar = SimpleTitleBar( self )
		self.layout().insertWidget( 0, self.titleBar )

	def event( self, ev ):
		e = ev.type()		
		if e == QEvent.KeyPress and ev.key() == Qt.Key_Escape:
			self.hide()

		elif e == QEvent.WindowDeactivate:
			self.hide()

		return super( SearchViewWidget, self ).event( ev )

	def sizeHint( self ):
		return QtCore.QSize( 300, 250 )

	def moveWindow( self, dx, dy ):
		pos = self.pos()
		self.move( pos.x() + dx, pos.y() + dy )

	def initEntries( self, entries ):
		self.entries = entries or []
		self.textTerms.setText('')
		self.textTerms.setFocus()		
		self.searchState = None
		self.updateVisibleEntries( self.entries, True )
		self.selectFirstItem()

	def updateVisibleEntries( self, entries, forceSort = False, **kwargs ):
		tree = self.treeResult
		tree.hide()
		root = tree.rootItem
		root.takeChildren()
		entriesOutput = entries
		# self.visEntries  = entries		
		sortMethod = kwargs.get( 'sort_method', self.defaultSortMethod or 'name' )
		if ( entries != self.entries ) or forceSort:
			keyFunc = None
			if sortMethod == 'score':
				keyFunc = cmp_to_key( _sortMatchScore )
			elif sortMethod == 'name':
				keyFunc = _keyFuncName
			elif sortMethod == 'none':
				keyFunc = False
			else:
				keyFunc = _keyFuncName
			
			if keyFunc:
				entriesOutput = sorted( entries, key = keyFunc )
			else:
				entriesOutput = entries[:]

		if len( entriesOutput ) > _SEARCHVIEW_ITEM_LIMIT:
			entriesOutput = entriesOutput[:_SEARCHVIEW_ITEM_LIMIT]

		for e in entriesOutput:
			if not e.treeItem:
				e.treeItem = tree.addNode( e )				 
			else:
				root.addChild( e.treeItem )
		tree.show()

	def updateSearchTerms( self, text ):
		def _buildREPattern( term ):
			pat = '.*'.join(map(re.escape, term))
			regex = re.compile(pat)
			return regex
		
		tree = self.treeResult
		# import pudb; pu.db
		if text and len(text) > 0:
			textU = text.upper()
			globs = textU.split()
			visEntries = []
			regexList = [ _buildREPattern( term ) for term in globs ]
			for entry in self.entries:
				if entry.matchQuery( globs, textU, regexList ):
					visEntries.append( entry )				
			self.updateVisibleEntries( visEntries, True, sort_method = 'score' )
		else:
			self.updateVisibleEntries( self.entries, True )
		self.selectFirstItem()

	def confirmSelection( self, obj ):
		self.selected = True
		if self.multipleSelection:
			result = []
			for entry in self.entries:
				if entry.checked:
					result.append( entry.obj )
			self.module.selectMultipleObjects( result )
		else:
			self.module.selectObject( obj )

	def testSelection( self, obj ):
		self.module.testSelection( obj )
	
	def onTermsChanged( self, text ):
		self.updateSearchTerms( text )

	def onSelectionChanged( self, selection ):
		self.module.notifySelectionChange( selection )

	def selectFirstItem( self ):
		# if not self.treeResult.getSelection():
		self.treeResult.clearSelection()
		item = self.treeResult.itemAt( 0, 0 )
		if item:
			item.setSelected( True )
			self.treeResult.scrollToItem( item )

	def onTermsReturn( self ):
		for node in self.treeResult.getSelection():
			self.confirmSelection( node.obj )
			return

	def hideEvent( self, ev ):
		if not self.searchState:
			self.module.cancelSearch()
		self.treeResult.clear()
		self.treeResult.clearFocus()
		self.textTerms.clearFocus()
		return super( SearchViewWidget, self ).hideEvent( ev )

	def focusResultTree( self ):
		self.selectFirstItem()
		self.treeResult.setFocus()

	def setInfo( self, text ):
		if self.titleBar:
			self.titleBar.setTitle( text or '' )
			self.ui.labelInfo.hide()
			return
			
		if text:
			self.ui.labelInfo.setText( text )
			self.ui.labelInfo.show()
		else:
			self.ui.labelInfo.hide()

	def setInitialSelection( self, selection ):
		if self.multipleSelection:
			if not selection: return
			for entry in self.entries:
				if entry.obj in selection:
					entry.checked = True
					self.treeResult.refreshNodeContent( entry )
		else:
			for entry in self.entries:
				if entry.obj == selection:
					self.treeResult.selectNode( entry, goto = True )
					break

	def setMultipleSelectionEnabled( self, enabled ):
		self.multipleSelection = enabled
		if enabled:
			self.treeResult.showColumn( 0 )
			self.treeResult.setColumnWidth( 0, 50 )
			self.treeResult.setColumnWidth( 1, 250 )
			self.treeResult.setColumnWidth( 2, 50 )
			self.ui.containerBottom.show()
		else:
			self.treeResult.hideColumn( 0 )
			self.treeResult.setColumnWidth( 0, 0 )
			self.treeResult.setColumnWidth( 1, 300 )
			self.treeResult.setColumnWidth( 2, 50 )
			self.ui.containerBottom.hide()

	def onButtonOK( self ):
		if self.multipleSelection:
			self.confirmSelection( None )

	def onButtonCancel( self ):
		self.hide()

	def onButtonAll( self ):
		if not self.multipleSelection: return
		for entry in self.entries:
			if not entry.checked:
				entry.checked = True
				self.treeResult.refreshNodeContent( entry )

	def onButtonInverse( self ):
		if not self.multipleSelection: return
		for entry in self.entries:
			entry.checked = not entry.checked
			self.treeResult.refreshNodeContent( entry )

	def onButtonNone( self ):
		if not self.multipleSelection: return
		for entry in self.entries:
			if entry.checked:
				entry.checked = False
				self.treeResult.refreshNodeContent( entry )

##----------------------------------------------------------------##
class SearchViewTextTerm( QtWidgets.QLineEdit):
	def keyPressEvent( self, ev ):
		key = ev.key()
		if key in [ Qt.Key_Down, Qt.Key_Up, Qt.Key_PageDown, Qt.Key_PageUp ] :
			self.browser.focusResultTree()
			self.browser.treeResult.keyPressEvent( ev )
			return
		return super( SearchViewTextTerm, self ).keyPressEvent( ev )

##----------------------------------------------------------------##
class SearchViewTree(GenericTreeWidget):
	def __init__( self, *args, **kwargs ):
		super( SearchViewTree, self ).__init__( *args, **kwargs )
		self.testingSelection = False
		self.setTextElideMode( Qt.ElideLeft )

	def getHeaderInfo( self ):
		return [('Sel', 50), ('Name', 650), ('Type', 80)]

	def getRootNode( self ):
		return self.browser

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass

	def getNodeParent( self, node ): # reimplemnt for target node	
		if node == self.getRootNode(): return None
		return self.getRootNode()
		
	def getNodeChildren( self, node ):
		if node == self.browser:
			return self.browser.entries
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self.getRootNode(): return
		item.setIcon( 0, getIcon( node.checked and 'checkbox_checked' or 'checkbox_unchecked' ) )
		item.setText( 1, node.name )
		item.setText( 2, node.typeName )
		if node.iconName:
			item.setIcon( 1, getIcon( node.iconName, 'default_item' ) )

	def onItemSelectionChanged(self):
		self.browser.onSelectionChanged( self.getSelection() )

	def createItem( self, node ):
		item = SearchViewItem()
		flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
		if self.option.get( 'editable', False ):
			flags |= Qt.ItemIsEditable 
		item.setFlags ( flags )
		return item

	def onClicked( self, item, col ):
		node = item.node
		if self.browser.multipleSelection:
			node.checked = not node.checked
			self.refreshNodeContent( node )
		else:
			self.browser.confirmSelection( node.obj )

	def onItemActivated( self, item, col ):
		node = item.node
		self.browser.confirmSelection( node.obj )

	def onClipboardCopy( self ):
		clip = QtWidgets.QApplication.clipboard()
		out = None
		for node in self.getSelection():
			if out:
				out += "\n"
			else:
				out = ""
			out += node.name
		clip.setText( out )
		return True

	def keyPressEvent(self, event):
		if not self.isVisible():
			return
			
		key = event.key()		
		if event.modifiers() in ( Qt.NoModifier, Qt.KeypadModifier) :
			if key in ( Qt.Key_Return, Qt.Key_Enter ):
				for node in self.getSelection():
					self.browser.confirmSelection( node.obj )
					return
			if ( int(key) >= int(Qt.Key_0) and int(key) <= int(Qt.Key_Z) ) \
				or key in [ Qt.Key_Delete, Qt.Key_Backspace, Qt.Key_Space ] :
				self.browser.textTerms.setFocus()
				self.browser.textTerms.keyPressEvent( event )
				return
			if key in ( Qt.Key_Right, Qt.Key_Left ):
				for node in self.getSelection():
					self.browser.testSelection( node.obj )
					return
		elif event.modifiers() in ( Qt.AltModifier, Qt.AltModifier | Qt.KeypadModifier ) \
			and key in ( Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right ):
			if key == Qt.Key_Up:
				self.browser.moveWindow( 0, -50 )
			elif key == Qt.Key_Down:
				self.browser.moveWindow( 0, 50 )
			elif key == Qt.Key_Left:
				self.browser.moveWindow( -50, 0 )
			elif key == Qt.Key_Right:
				self.browser.moveWindow( 50, 0 )

		elif key == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
			self.browser.textTerms.setFocus()
			self.browser.textTerms.keyPressEvent( event )
			return

		return super( SearchViewTree, self ).keyPressEvent( event )

##----------------------------------------------------------------##
class SearchEntry(object):
	def __init__( self, obj, name, typeName, iconName ):
		self.visible    = False
		self.treeItem   = None
		self.matchScore = 0
		self.obj        = obj
		self.name       = name
		if isinstance( name, str ):
			name = str( name )
		if isinstance( typeName, str ):
			typeName = str( typeName )
		self.typeName   = typeName
		self.iconName   = iconName
		self.typeNameU  = typeName.upper()
		self.nameU      = name.upper()
		self.compareStr = typeName + ': ' + name
		self.checked    = False	

	def getTypeName( self ):
		return self.typeName
		
	def getName( self ):
		return self.name

	def getObject( self ):
		return self.obj

	def matchQuery( self, globs, text, regexList ):
		score = float(0.0)
		findInType = False
		findInName = False
		findCount  = 0
		termCount  = len( regexList )
		name = self.nameU
		typeName = self.typeNameU
		size = len( name )

		for regex in regexList:
			if regex.search( name ):
				findInName = True
				findCount += 1
				if regex.search( typeName ):
					findInType = True
			else:
				if regex.search( typeName ):
					findCount += 1

		if findCount < termCount:
			return False
		
		if findInName:
			for t in globs:
				pos = name.find( t )
				if pos >= 0:
					k = float(pos)/size - 0.5
					score += ( k*k * 0.5 + 0.5 )
				score += ( ratio( t, name ) * 0.1 )
		
		if findInType:
			score += 1.0
			score *= 1.5

		self.matchScore = score

		return score > 0

##----------------------------------------------------------------##
class SearchView( EditorModule ):	
	def __init__( self ):
		self.enumerators = []
		self.onCancel    = None
		self.onSelection = None
		self.onTest      = None
		self.visEntries  = None

	def getName( self ):
		return 'search_view'

	def getDependency( self ):
		return ['qt']

	def onLoad( self ):
		self.window = SearchViewWidget( None )
		self.window.module = self

	def request( self, **option ):
		pos        = option.get( 'pos', QtGui.QCursor.pos() )
		
		typeId     = option.get( 'type',    None )
		context    = option.get( 'context', None )
		terms      = option.get( 'terms',   None )
		
		info         = option.get( 'info', None )
		initial      = option.get( 'initial', None )
		multiple     = option.get( 'multiple_selection', False )
		searchOption = option.get( 'option', None )

		self.onSelection = option.get( 'on_selection', None )
		self.onCancel    = option.get( 'on_cancel',    None )
		self.onTest      = option.get( 'on_test',    None )
		self.onChange    = option.get( 'on_change', None )
		self.defaultSortMethod    = option.get( 'sort_method',  None )
		#TODO: allow use list/dict for search candinates.
		# if isinstance( onSearch, list ): pass
		self.window.move( pos )
		

		self.window.defaultSortMethod = self.defaultSortMethod
		self.window.show()
		self.window.raise_()
		# self.window.setFocus()
		restrainWidgetToScreen( self.window )
		self.window.treeResult.setFocus()
		# self.window.setFocus()
		self.window.setInfo( info )

		#alternative candidtate provider
		onSearch   = option.get( 'on_search',  None )
		selections = option.get( 'selections', None )

		entries = self.enumerateSearch( typeId, context, onSearch, selections, searchOption )
		self.window.initEntries( entries )
	
		self.window.setMultipleSelectionEnabled( multiple )
		if initial:
			self.window.setInitialSelection( initial )
		if terms:
			self.window.textTerms.setText( terms )
			self.window.updateSearchTerms( terms )

	def requestSearch( self, **option ):
		typeId       = option.get( 'type',       None )
		context      = option.get( 'context',    None )
		onSearch     = option.get( 'on_search',  None )
		selections   = option.get( 'selections', None )
		searchOption = option.get( 'option',     {} )
		entries = self.enumerateSearch( typeId, context, onSearch, selections, searchOption )
		return entries

	def selectObject( self, obj ):
		if self.window.searchState: return
		self.window.searchState = 'selected'
		self.window.hide()
		if self.onSelection:
			self.onSelection( obj )

	def selectMultipleObjects( self, objs ):
		if self.window.searchState: return
		self.window.searchState = 'selected'
		self.window.hide()
		if self.onSelection:
			self.onSelection( objs )

	def notifySelectionChange( self, selection ):
		if self.window.searchState: return
		if self.onChange:
			self.onChange( selection )

	def testSelection( self, obj ):
		if self.window.searchState: return
		if self.onTest:
			self.onTest( obj )	

	def cancelSearch( self ):
		if self.window.searchState: return
		self.window.searchState = 'cancel'
		self.window.hide()
		if self.onCancel:
			self.onCancel()

	def registerSearchEnumerator( self, enumerator ):
		#format [  ( obj,  objName, objTypeName, objIcon ), ...  ] or None
		self.enumerators.append( enumerator )

	def enumerateSearch( self, typeId, context, onSearch, selections, searchOption = None ):
		allResult = []
		if onSearch:
			allResult = onSearch( typeId, context, searchOption or {} )
		elif selections:
			allResult = selections
		else:
			for e in self.enumerators:
				result = e( typeId, context, searchOption or {} )
				if result:
					allResult += result
		return [ SearchEntry( *r ) for r in allResult ]

##----------------------------------------------------------------##
class SearchViewItem( QtWidgets.QTreeWidgetItem ):
	def __lt__( self, other ):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node1:
			return True
		t0 = - node0.matchScore
		t1 = - node1.matchScore
		if t0 < t1: return True
		if t0 == t1 : return node0.name < node1.name
		return False
		
##----------------------------------------------------------------##
searchView = SearchView()
searchView.register()
def requestSearchView( **option ):
	return searchView.request( **option )

def requestSearch( **option ):
	return searchView.requestSearch( **option )

def requestSearchView_dict( option ): #support for lua accessing
	return searchView.request( **option )

def requestSearch_dict( option ):
	return searchView.requestSearch( **option )

def registerSearchEnumerator( enumerator ):
	searchView.registerSearchEnumerator( enumerator )


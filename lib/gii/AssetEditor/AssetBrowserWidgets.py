import random
import json
import os

from qtpy            import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore     import Qt, QSize

from qtpy.QtGui      import QBrush, QColor
from qtpy.QtWidgets import QApplication, QStyle

from gii.core         import *
from gii.qt           import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.qt.controls.GenericListWidget import GenericListWidget, GenericListFilter
from gii.qt.controls.ElidedLabel       import ElidedLabel
from gii.qt.controls.SearchFilterWidget import SearchFilterWidget
from gii.qt.dialogs   import requestString, alertMessage, requestConfirm


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
def makeAssetListMimeData( assets ):
	assetList = []
	urlList   = []
	
	for asset in assets:
		assetList.append( asset.getPath() )
		if not asset.isVirtual():
			urlList.append( QtCore.QUrl.fromLocalFile( asset.getAbsFilePath() ) )
	assetListData = json.dumps( assetList ).encode('utf-8')
	
	text = '\n'.join( assetList )

	data = QtCore.QMimeData()
	data.setData( GII_MIME_ASSET_LIST, assetListData )
	if urlList:
		data.setUrls( urlList )
	data.setText( text )
	return data

##----------------------------------------------------------------##
class AssetFolderTreeFilter( GenericTreeFilter ):
	pass

##----------------------------------------------------------------##
#TODO: allow sort by other column
class AssetTreeItem(QtWidgets.QTreeWidgetItem):
	def __lt__(self, other):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node0:
			return False
		if not node1:
			return True
		tree = self.treeWidget()

		# if not tree:
		# 	col = 0
		# else:
		# 	col = tree.sortColumn()		
		t0 = node0.getType()
		t1 = node1.getType()
		if t1!=t0:			
			if tree.sortOrder() == 0:
				if t0 == 'folder': return True
				if t1 == 'folder': return False
			else:
				if t0 == 'folder': return False
				if t1 == 'folder': return True
		return super( AssetTreeItem, self ).__lt__( other )
		# return node0.getName().lower()<node1.getName().lower()

##----------------------------------------------------------------##
class AssetFolderTreeView( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		option[ 'show_root' ] = True
		super( AssetFolderTreeView, self ).__init__( *args, **option )
		self.refreshingSelection = False
		self.setHeaderHidden( True )

	def saveTreeStates( self ):
		for node, item in list(self.nodeDict.items()):
			node.setProperty( 'expanded', item.isExpanded() )

	def loadTreeStates( self ):
		for node, item in list(self.nodeDict.items()):
			item.setExpanded( node.getProperty( 'expanded', False ) )
		self.getItemByNode( self.getRootNode() ).setExpanded( True )
		
	def getRootNode( self ):
		return app.getAssetLibrary().getRootNode()

	def getNodeParent( self, node ): # reimplemnt for target node
		return node.getParent()

	def getNodeChildren( self, node ):
		result = []
		for node in node.getChildren():
			if node.getProperty( 'hidden', False ): continue
			if not node.getGroupType() in ( 'folder', 'package' ) :continue
			result.append( node )
		return result

	def createItem( self, node ):
		return AssetTreeItem()

	def mimeData( self, items ):
		return makeAssetListMimeData( [ item.node for item in items ])

	def updateItemContent( self, item, node, **option ):
		assetType = node.getType()
		item.setText( 0, node.getName() )
		iconName = app.getAssetLibrary().getAssetIcon( assetType )
		item.setIcon(0, getIcon(iconName,'normal'))
		remoteNode = node.getRemoteFileNode()
		if remoteNode:
			item.setForeground( 0, QColor('#4ee4ff') )
		else:
			if node.isParentRemoteFile():
				item.setForeground( 0, QColor('#7990c4') )
			else:
				item.setForeground( 0, QColor('#ccc') )

	def onClipboardCopy( self ):
		clip = QtWidgets.QApplication.clipboard()
		modifiers = QApplication.keyboardModifiers()
		out = None
		for node in self.getSelection():
			if out:
				out += "\n"
			else:
				out = ""
			if modifiers & Qt.ShiftModifier:
				out += node.getName()
			else:
				out += node.getNodePath()
		clip.setText( out )
		return True

	def getHeaderInfo( self ):
		return [ ('Name',120) ]

	def _updateItem(self, node, updateLog=None, **option):
		super( AssetFolderTreeView, self )._updateItem( node, updateLog, **option )

		if option.get('updateDependency',False):
			for dep in node.dependency:
				self._updateItem(dep, updateLog, **option)

	def onClicked(self, item, col):
		pass

	def onItemActivated(self, item, col):
		node=item.node
		self.owner.onActivateNode( node, 'tree' )

	def onItemSelectionChanged(self):
		self.owner.onTreeSelectionChanged()

	def onDeletePressed( self ):
		self.owner.onTreeRequestDelete()
		

##----------------------------------------------------------------##

class AssetListItemDelegate( QtWidgets.QStyledItemDelegate ):
	pass
	# def initStyleOption(self, option, index):
	# 	# let the base class initStyleOption fill option with the default values
	# 	super( AssetListItemDelegate, self ).initStyleOption(option, index)
	# 	# override what you need to change in option
	# 	if option.state & QStyle.State_Selected:
	# 		# option.state &= ~ QStyle.State_Selected
	# 		option.backgroundBrush = QBrush(QColor(100, 200, 100, 200))
		
##----------------------------------------------------------------##
class AssetBrowserIconListWidget( GenericListWidget ):
	def __init__( self, *args, **option ):
		option[ 'mode' ] = 'icon'
		option[ 'drag_mode' ] = 'all'
		option[ 'multiple_selection' ] = True
		super( AssetBrowserIconListWidget, self ).__init__( *args, **option )
		self.setObjectName( 'AssetBrowserList' )
		self.setWrapping( True )
		self.setLayoutMode( QtWidgets.QListView.SinglePass )
		# self.setLayoutMode( QtWidgets.QListView.Batched )
		self.setResizeMode( QtWidgets.QListView.Adjust  )
		self.setHorizontalScrollMode( QtWidgets.QAbstractItemView.ScrollPerPixel )
		self.setVerticalScrollMode( QtWidgets.QAbstractItemView.ScrollPerPixel )
		# self.setMovement( QtWidgets.QListView.Static )
		self.setMovement( QtWidgets.QListView.Snap )
		self.setTextElideMode( Qt.ElideRight )
		
		self.thumbnailIconSize = ( 80, 80 )
		# self.setIconSize( QtCore.QSize( 32, 32 ) )
		self.setItemDelegate( AssetListItemDelegate( self ) )
		
		self.setIconSize( QtCore.QSize( 120, 130 ) )
		self.setGridSize( QtCore.QSize( 120, 130 ) )
		self.setWordWrap( True )


	def getItemFlags( self, node ):
		return {}

	def getDefaultOptions( self ):
		return None

	def getNodes( self ):
		return self.owner.getAssetsInList()

	def updateItemContent( self, item, node, **option ):
		rawName = node.getName()
		dotIdx = rawName.find( '.' )
		if dotIdx > 0:
			name = rawName[ 0:dotIdx ]
			ext  = rawName[ dotIdx: ]
			item.setText( name + '\n' + ext )
		else:
			item.setText( rawName )
		thumbnailIcon = self.owner.getAssetThumbnailIcon( node, self.thumbnailIconSize )
		if not thumbnailIcon:
			thumbnailIcon = getIcon( 'thumbnail/%s' % node.getType(), 'thumbnail/default' )

		item.setIcon( thumbnailIcon )
		item.setSizeHint( QtCore.QSize( 120, 130 ) )
		# item.setTextAlignment( Qt.AlignLeft | Qt.AlignVCenter )
		item.setTextAlignment( Qt.AlignCenter | Qt.AlignVCenter )
		item.setToolTip( node.getPath() )
		remoteNode = node.getRemoteFileNode()
		if remoteNode:
			item.setForeground( QColor('#4ee4ff') )
		else:
			if node.isParentRemoteFile():
				item.setForeground( QColor('#7990c4') )
			else:
				item.setForeground( QColor('#ccc') )

	def onItemSelectionChanged(self):
		self.owner.onListSelectionChanged()

	def onItemActivated( self, item ):
		node = item.node
		self.owner.onActivateNode( node, 'list' )

	def mimeData( self, items ):
		return makeAssetListMimeData( [ item.node for item in items ])
		
	def onDeletePressed( self ):
		self.owner.onListRequestDelete()

	def onClipboardCopy( self ):
		clip = QtWidgets.QApplication.clipboard()
		nameOnly = QApplication.keyboardModifiers() & Qt.ShiftModifier
		if nameOnly:
			clip.setText( '\n'.join( [ node.getName() for node in self.getSelection() ] ) )
		else:
			clip.setMimeData( makeAssetListMimeData( self.getSelection() ) )
		return True

	def onClipboardPaste( self ):
		clip = QtWidgets.QApplication.clipboard()
		data = clip.mimeData()
		if data.hasFormat( GII_MIME_ASSET_LIST ):
			assetList = json.loads( str(mime.data( GII_MIME_ASSET_LIST )), 'utf-8' )
			for path in assetList:			
				asset = assetLib.getAssetNode( path )
				if asset:
					#TODO: clone asset
					pass
		elif data.hasUrls():
			localFiles = []
			for url in data.urls():
				if url.isLocalFile():
					localFiles.append( url.path() )
			if localFiles:
				self.owner.pasteLocalFiles( localFiles )


##----------------------------------------------------------------##
class AssetBrowserDetailListWidget( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		option[ 'drag_mode' ] = 'all'
		option[ 'multiple_selection' ] = True
		super( AssetBrowserDetailListWidget, self ).__init__( *args, **option )
		self.setObjectName( 'AssetBrowserDetailList' )
		self.setIndentation( 0 )

	def getHeaderInfo( self ):
		return [ ('Name',150), ('Type', 80), ( 'Desc', 50 ) ]

	def getRootNode( self ):
		return self.owner

	def getNodeParent( self, node ): # reimplemnt for target node	
		if node == self.owner: return None
		return self.owner

	def getNodeChildren( self, node ):
		if node == self.owner:
			return self.owner.getAssetsInList()
		else:
			return []

	def createItem( self, node ):
		return AssetTreeItem()
		
	def updateItemContent( self, item, node, **option ):
		if node == self.owner: return 
		assetType = node.getType()
		item.setText( 0, node.getName() )
		iconName = app.getAssetLibrary().getAssetIcon( assetType )
		item.setIcon(0, getIcon(iconName,'normal'))
		item.setText( 1, assetType )
		remoteNode = node.getRemoteFileNode()
		if remoteNode:
			item.setForeground( 0, QColor('#4ee4ff') )
		else:
			if node.isParentRemoteFile():
				item.setForeground( 0, QColor('#7990c4') )
			else:
				item.setForeground( 0, QColor('#ccc') )

	def mimeData( self, items ):
		return makeAssetListMimeData( [ item.node for item in items ])
		
	def onItemSelectionChanged(self):
		self.owner.onListSelectionChanged()

	def onItemActivated( self, item, col ):
		node = item.node
		self.owner.onActivateNode( node, 'list' )

	def onDeletePressed( self ):
		self.owner.onListRequestDelete()

	def onClipboardCopy( self ):
		clip = QtWidgets.QApplication.clipboard()
		nameOnly = QApplication.keyboardModifiers() & Qt.ShiftModifier
		if nameOnly:
			clip.setText( '\n'.join( [ node.getName() for node in self.getSelection() ] ) )
		else:
			clip.setMimeData( makeAssetListMimeData( self.getSelection() ) )
		return True

	def onClipboardPaste( self ):
		clip = QtWidgets.QApplication.clipboard()
		data = clip.mimeData()
		if data.hasFormat( GII_MIME_ASSET_LIST ):
			assetList = json.loads( str(mime.data( GII_MIME_ASSET_LIST )), 'utf-8' )
			for path in assetList:			
				asset = assetLib.getAssetNode( path )
				if asset:
					#TODO: clone asset
					pass
		elif data.hasUrls():
			localFiles = []
			for url in data.urls():
				if url.isLocalFile():
					localFiles.append( url.path() )
			if localFiles:
				self.owner.pasteLocalFiles( localFiles )

##----------------------------------------------------------------##
class AssetBrowserTagFilterWidget( SearchFilterWidget ):
	def __init__( self, *args, **kwargs ):
		super( AssetBrowserTagFilterWidget, self ).__init__( *args, **kwargs )
		self.filterChanged.connect( self.onFilterChanged )
	
	def onFilterChanged( self ):
		self.owner.updateTagFilter()

	# def onActionAdd( self ):
	# 	pass

	# def onActionLock( self ):
	# 	pass
		
	# def onActionEdit( self ):
	# 	pass
		
	# def onActionDelete( self ):
	# 	pass
		

##----------------------------------------------------------------##
class AssetBrowserStatusBar( QtWidgets.QFrame ):
	def __init__( self, *args, **kwargs ):
		super( AssetBrowserStatusBar, self ).__init__( *args, **kwargs )
		layout = QtWidgets.QVBoxLayout( self )
		layout.setSpacing( 1 )
		layout.setContentsMargins( 1 , 1 , 1 , 1 )

		self.textStatus = ElidedLabel( self )
		self.textStatus.setMinimumHeight( 15 )
		self.tagsBar = AssetBrowserStatusBarTag( self )
		layout.addWidget( self.tagsBar )
		layout.addWidget( self.textStatus )
		self.tagsBar.buttonEdit.clicked.connect( self.onButtonEditTags )

	def onButtonEditTags( self ):
		self.owner.editAssetTags()

	def setText( self, text ):
		self.textStatus.setText( text )

	def setTags( self, text ):
		self.tagsBar.setText( text )

##----------------------------------------------------------------##
class AssetBrowserStatusBarTag( QtWidgets.QFrame ):
	def __init__( self, *args, **kwargs ):
		super( AssetBrowserStatusBarTag, self ).__init__( *args, **kwargs )
		layout = QtWidgets.QHBoxLayout( self )
		layout.setSpacing( 1 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		self.textTags = QtWidgets.QLabel( self )
		self.textTags.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
		self.buttonEdit = QtWidgets.QToolButton( self )
		self.buttonEdit.setIconSize( QSize( 16,10 ) )
		self.buttonEdit.setIcon( getIcon( 'tag-2' ) )
		layout.addWidget( self.buttonEdit )
		layout.addWidget( self.textTags )

	def setText( self, text ):
		self.textTags.setText( text )

##----------------------------------------------------------------##
class AssetBrowserNavigatorCrumbBar( QtWidgets.QWidget ):
	pass

##----------------------------------------------------------------##
class AssetBrowserNavigator( QtWidgets.QWidget ):
	def __init__( self, *args, **kwargs ):
		super( AssetBrowserNavigator, self ).__init__( *args, **kwargs )
		layout = QtWidgets.QHBoxLayout( self )
		layout.setSpacing( 1 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		self.buttonUpper    = QtWidgets.QToolButton()
		self.buttonForward  = QtWidgets.QToolButton()
		self.buttonBackward = QtWidgets.QToolButton()
		self.buttonUpper.setIconSize( QSize( 16, 16 )  )
		self.buttonForward.setIconSize( QSize( 16, 16 )  )
		self.buttonBackward.setIconSize( QSize( 16, 16 )  )
		self.buttonUpper.setIcon( getIcon( 'upper_folder' ) )
		self.buttonForward.setIcon( getIcon( 'history_forward' ) )
		self.buttonBackward.setIcon( getIcon( 'history_backward' ) )
		layout.addWidget( self.buttonUpper )
		layout.addSpacing( 10 )
		layout.addWidget( self.buttonBackward )
		layout.addWidget( self.buttonForward )
		self.buttonUpper.clicked.connect( self.onGoUpperLevel )
		self.buttonForward.clicked.connect( self.onHistoryForward )
		self.buttonBackward.clicked.connect( self.onHistoryBackward )

		self.crumbBar = AssetBrowserNavigatorCrumbBar()
		layout.addWidget( self.crumbBar )
		self.crumbBar.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )

	def onHistoryForward( self ):
		self.owner.forwardHistory()

	def onGoUpperLevel( self ):
		self.owner.goUpperLevel()

	def onHistoryBackward( self ):
		self.owner.backwardHistory()


##----------------------------------------------------------------##
class AssetFilterTreeFilter( GenericTreeFilter ):
	pass

##----------------------------------------------------------------##
#TODO: allow sort by other column
class AssetFilterTreeItem(QtWidgets.QTreeWidgetItem):
	def __lt__(self, other):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node1:
			return True
		tree = self.treeWidget()

		t0 = node0.getType()
		t1 = node1.getType()
		if t1!=t0:			
			if tree.sortOrder() == 0:
				if t0 == 'group': return True
				if t1 == 'group': return False
			else:
				if t0 == 'group': return False
				if t1 == 'group': return True
		return super( AssetFilterTreeItem, self ).__lt__( other )
		# return node0.getName().lower()<node1.getName().lower()

##----------------------------------------------------------------##
class AssetFilterTreeView( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		option[ 'show_root' ] = False
		option[ 'editable'  ] = True

		super( AssetFilterTreeView, self ).__init__( *args, **option )
		self.setHeaderHidden( True )

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass
		
	def getRootNode( self ):
		return self.owner.getFilterRootGroup()

	def getNodeParent( self, node ): # reimplemnt for target node
		return node.getParent()

	def getNodeChildren( self, node ):
		result = []
		for node in node.getChildren():
			result.append( node )
		return result

	def createItem( self, node ):
		return AssetFilterTreeItem()

	def updateItemContent( self, item, node, **option ):
		t = node.getType()
		item.setText( 0, node.getName() )
		if t == 'group':
			item.setIcon(0, getIcon( 'folder-tag' ) )
		else:
			item.setIcon(0, getIcon( 'asset-filter' ) )

	def getHeaderInfo( self ):
		return [ ('Name',120) ]

	def onClicked(self, item, col):
		pass

	def onItemSelectionChanged(self):
		for f in self.getSelection():
			self.owner.setAssetFilter( f )

	def onItemChanged( self, item, col ):
		node = self.getNodeByItem( item )
		self.owner.renameFilter( node, item.text( 0 ) )
		
	def onDeletePressed( self ):
		for f in self.getSelection():
			self.owner.onAsseotFilterRequestDelete( f )
		
		

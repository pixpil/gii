import sys
import math

from gii.qt.controls.GraphicsView.TimelineView import *
from gii.qt.controls.GenericTreeWidget     import GenericTreeWidget, GenericTreeFilter
from gii.qt.controls.PropertyEditor        import PropertyEditor
from gii.qt.IconCache                      import getIcon
from gii.qt.helpers                        import addWidgetWithLayout, QColorF, unpackQColor

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QSize
from qtpy.QtGui import QColor, QTransform

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance


_TRACK_SIZE = 20

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

AnimatorWidgetUI,BaseClass = uic.loadUiType( _getModulePath('animator.ui') )

class AnimatorTrackTreeItemDelegate( QtWidgets.QStyledItemDelegate ):
	def sizeHint( self, option, index ):
		return QSize( 10, _TRACK_SIZE )

class AnimatorTrackTreeItem(QtWidgets.QTreeWidgetItem):
	def __lt__(self, other):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node1:
			return True
		tree = self.treeWidget()

		# if not tree:
		# 	col = 0
		# else:
		# 	col = tree.sortColumn()
		t0 = isMockInstance( node0, 'AnimatorTrackGroup' ) and 'group' or 'node'
		t1 = isMockInstance( node1, 'AnimatorTrackGroup' ) and 'group' or 'node'

		if t1!=t0:			
			if tree.sortOrder() == 0:
				if t0 == 'group': return True
				if t1 == 'group': return False
			else:
				if t0 == 'group': return False
				if t1 == 'group': return True
		return super( AnimatorTrackTreeItem, self ).__lt__( other )
		# return node0.getName().lower()<node1.getName().lower()

##----------------------------------------------------------------##
class AnimatorTrackTree( GenericTreeWidget ):
	layoutChanged = Signal()
	def __init__( self, *args, **option ):
		option['editable']  = True
		option['drag_mode'] = 'internal'
		option['multiple_selection'] = True
		# option['alternating_color'] = True
		super( AnimatorTrackTree, self ).__init__( *args, **option )
		self.setItemDelegate( AnimatorTrackTreeItemDelegate() )
		self.setVerticalScrollMode( QtWidgets.QAbstractItemView.ScrollPerPixel )
		self.adjustingRange = False
		self.verticalScrollBar().rangeChanged.connect( self.onScrollRangeChanged )		
		self.setIndentation( 14 )
		self.setAttribute(Qt.WA_MacShowFocusRect, False)
		self.setTextElideMode( Qt.ElideMiddle )

	def event( self, ev ):
		if ev.type() == 1:
			self.parentView.updateTrackLayout()
		return super( AnimatorTrackTree, self ).event( ev )

	def getHeaderInfo( self ):
		return [ ('Name',70), ('Key', 20), ('Act',20) ]

	def resetHeader( self ):
		super( AnimatorTrackTree, self ).resetHeader()
		self.fitColumnSize()

	def getRootNode( self ):
		return self.owner.getClipRoot()

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		for node, item in list(self.nodeDict.items()):
			if not item: continue
			expanded = not node._folded
			item.setExpanded( expanded )

	def createItem( self, node ):
		return AnimatorTrackTreeItem()

	def getNodeParent( self, node ): # reimplemnt for target node	
		return node.parent

	def getNodeChildren( self, node ):
		return [ clip for clip in list(node.children.values()) ]

	def getItemFlags( self, node ):
		flags = {}
		if isMockInstance( node, 'AnimatorTrackGroup' ):
			flags['editable'] = True
		else:
			flags['editable'] = False
		return flags

	def updateItemContent( self, item, node, **option ):
		pal = self.palette()
		defaultBrush = QColorF( .8,.8,.8 )
		name = None

		if isMockInstance( node, 'AnimatorTrackGroup' ):
			item.setText( 0, node.toString( node ) )
			item.setToolTip( 0, node.toString( node ) )
			item.setIcon( 0, getIcon('track_group') )
		elif isMockInstance( node, 'AnimatorClipSubNode' ):
			item.setText( 0, node.toString( node ) )
			item.setToolTip( 0, node.toString( node ) )
			item.setIcon( 0, getIcon(node.getIcon( node )) )
			if node.isCurveTrack( node ):
				item.setIcon( 1, getIcon('track_key_0') )
			else:
				item.setIcon( 1, getIcon('track_key_none') )
		if node.isLocalActive( node ):
			item.setIcon( 2, getIcon('track_active') )
		else:
			item.setIcon( 2, getIcon('track_inactive') )
		
	def onItemSelectionChanged(self):
		self.parentView.onTrackSelectioChanged()

	def onItemChanged( self, item, col ):
		self.owner.renameTrack( item.node, item.text(0) )

	def resizeEvent( self, event ):
		super( AnimatorTrackTree, self ).resizeEvent( event )
		self.fitColumnSize()

	def fitColumnSize( self ):
		width = self.width() - 4
		self.setColumnWidth ( 0, width - 22*2 )
		self.setColumnWidth ( 1, 22 )
		self.setColumnWidth ( 2, 22 )

	def onItemExpanded( self, item ):
		if self.rebuilding: return
		node = item.node
		self.parentView.onTrackFolded( node, False )

	def onItemCollapsed( self, item ):
		if self.rebuilding: return
		node = item.node
		self.parentView.onTrackFolded( node, True )

	def onScrollRangeChanged( self, min, max ):
		if self.adjustingRange: return
		self.adjustingRange = True
		maxRange = max + self.height() - 25
		self.verticalScrollBar().setRange( min, maxRange )
		self.parentView.setTrackViewScrollRange( maxRange )
		self.adjustingRange = False

	def mousePressEvent( self, ev ):
		item = self.itemAt( ev.pos() )
		if not item:
			self.clearSelection()
		else:
			if ev.button() == Qt.LeftButton:
				col = self.columnAt( ev.pos().x() )
				if col == 2:
					node = self.getNodeByItem( item )
					self.parentView.owner.toggleTrackActive( node )
					self.refreshNodeContent( node )
					return
			
		return super( AnimatorTrackTree, self ).mousePressEvent( ev )

	def dropEvent( self, ev ):		
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
		
		if pos == 'above' or pos =='below':
			#TODO: reorder
			ev.setDropAction( Qt.IgnoreAction )
			return

		target = self.itemAt( ev.pos() )
		source = self.getSelection()

		if pos == 'on':
			targetTrack = target.node
		else:
			targetTrack = 'root'

		succ = self.owner.doCommand( 
			'scene_editor/animator_reparent_track', 
			source = source,
			target = targetTrack
		)
		
		if not succ:
			ev.setDropAction( Qt.IgnoreAction )
		else:
			ev.acceptProposedAction()
			self.rebuild()



##----------------------------------------------------------------##
class AnimatorClipListTreeItem(QtWidgets.QTreeWidgetItem):
	def __lt__(self, other):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node1:
			return True
		tree = self.treeWidget()

		# 	col = tree.sortColumn()
		t0 = isMockInstance( node0, 'AnimatorClipGroup' ) and 'group' \
			or isMockInstance( node0, 'AnimatorClipTree' ) and 'tree' \
			or 'clip'

		t1 = isMockInstance( node1, 'AnimatorClipGroup' ) and 'group' \
			or isMockInstance( node1, 'AnimatorClipTree' ) and 'tree' \
			or 'clip'

		if t1!=t0:
			if tree.sortOrder() == 0:
				if t0 == 'group': return True
				if t1 == 'group': return False
				if t0 == 'tree' : return True
				if t1 == 'tree' : return False
			else:
				if t0 == 'group': return False
				if t1 == 'group': return True
				if t0 == 'tree' : return False
				if t1 == 'tree' : return True
		return super( AnimatorClipListTreeItem, self ).__lt__( other )


##----------------------------------------------------------------##
class AnimatorClipListTree( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		option['drag_mode'] = 'internal'
		super( AnimatorClipListTree, self ).__init__( *args, **option )
		self.setIndentation( 10 )		
		self.option['editable'] = True


	def createItem( self, node ):
		return AnimatorClipListTreeItem()

	def getHeaderInfo( self ):
		return [ ('Name',50) ]

	def getRootNode( self ):
		return self.owner.getRootClipGroup()

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		for node, item in list(self.nodeDict.items()):
			if not item: continue
			expanded = not node._folded
			item.setExpanded( expanded )

	def onItemExpanded( self, item ):
		if self.rebuilding: return
		node = item.node
		node._folded = False

	def onItemCollapsed( self, item ):
		if self.rebuilding: return
		node = item.node
		node._folded = True

	def getNodeParent( self, node ): # reimplemnt for target node	
		return node.parentGroup

	def getNodeChildren( self, node ):
		if isMockInstance( node, 'AnimatorClipGroup' ):
			children = node.getChildNodes( node )
			return [ child for child in list(children.values()) ]
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if isMockInstance( node, 'AnimatorClipGroup' ):
			# pal = self.palette()
			# defaultBrush = QColorF( .8,.8,.8 )
			# name = None
			item.setText( 0, node.name )
			item.setIcon( 0, getIcon('folder') )

		elif isMockInstance( node, 'AnimatorClipTree' ):
			item.setText( 0, node.name )
			item.setIcon( 0, getIcon('clip_tree') )

		else:
			item.setText( 0, node.name )
			item.setIcon( 0, getIcon('clip') )
		
	def onItemSelectionChanged(self):
		self.parentView.onClipSelectioChanged()

	def onItemChanged( self, item, col ):
		self.owner.renameClip( item.node, item.text(0) )

	def dropEvent( self, ev ):		
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

		target = self.itemAt( ev.pos() )
		source = self.getSelection()

		if pos == 'on':
			targetClip = target.node
		else:
			targetClip = 'root'

		succ = self.owner.doCommand( 
			'scene_editor/animator_reparent_clip', 
			source = source,
			target = targetClip
		)
		
		if not succ:
			ev.setDropAction( Qt.IgnoreAction )
		else:
			ev.acceptProposedAction()
			self.rebuild()


##----------------------------------------------------------------##
class AnimatorTimelineWidget( TimelineView ):
	def hasCurveView( self ):
		return True

	def getTrackNodes( self ):
		return self.owner.getTrackList()

	def getMarkerNodes( self ):
		return self.owner.getMarkerList()

	def getKeyNodes( self, trackNode ):
		keys = trackNode['keys']
		if keys:
			return [ key for key in list(keys.values()) ]
		else:
			return []

	def getParentKeyNode( self, keyNode ):
		return keyNode.parentKey or None

	def getChildKeyNodes( self, keyNode ):
		if keyNode.childKeys:
			return list(keyNode.childKeys.values())
		else:
			return []

	def getParentTrackNode( self, keyNode ):
		return keyNode['parent']

	def getTrackPos( self, trackNode ):
		return self.parentView.getTrackPos( trackNode )

	def isTrackVisible( self, trackNode ):
		return self.parentView.isTrackVisible( trackNode )

	def updateTrackContent( self, track, trackNode, **option ):
		# trackType = trackNode.getType( trackNode )
		# iconName = 'track_%s' % trackType
		# icon = getIcon( iconName ) or getIcon( 'obj' )
		# track.getHeader().setText( trackNode.name )
		# track.getHeader().setIcon( icon )
		pass

	def updateMarkerContent( self, marker, markerNode, **option ):
		name = markerNode.getName( markerNode )
		marker.setText( name )

	def updateKeyContent( self, key, keyNode, **option ):
		text = keyNode.toString( keyNode )
		key.setText( text )

	def getMarkerParam( self, markerNode ):
		return markerNode.getPos( markerNode )

	def getKeyParam( self, keyNode ):
		resizable = keyNode.isResizable( keyNode )
		length    = resizable and keyNode.length or 0
		return keyNode.getPos( keyNode ), length, resizable

	def getKeyCurveValue( self, keyNode ):
		value = keyNode.getCurveValue( keyNode )
		return value

	def getKeyTweenMode( self, keyNode ):
		mode = keyNode.getTweenMode( keyNode )
		if mode == 0:
			return TWEEN_MODE_LINEAR
		elif mode == 1:
			return TWEEN_MODE_CONSTANT
		elif mode == 2:
			return TWEEN_MODE_BEZIER
		else:
			return TWEEN_MODE_LINEAR

	def isCurveTrack( self, trackNode ):
		return trackNode.isCurveTrack( trackNode )

	def getKeyBezierPoints( self, keyNode ):
		( bpx0, bpy0, bpx1, bpy1 ) = keyNode.getBezierPoints( keyNode )
		return ( -bpx0, bpy0, bpx1, bpy1 )

	def getClipRange( self ):
		t = self.parentView.owner.getTargetClipLength()
		return 0, t
		
	def onSelectionChanged( self, selection ):
		if selection:
			self.parentView.setPropertyTarget( selection[0] )
		else:
			self.parentView.setPropertyTarget( None )

	def onMarkerSelectionChanged( self, markerSelection ):
		if markerSelection:
			self.parentView.setPropertyTarget( markerSelection[0] )
		else:
			self.parentView.setPropertyTarget( None )

	def formatPos( self, pos ):
		i = int( pos/1000 )
		f = int( pos - i*1000 )
		return '%d:%02d' % ( i, f/10 )

	def getRulerParam( self ):
		return dict( zoom = 0.1, pos_step = 1000, sub_step = 100 )

	def createTrackItem( self, trackNode, **options ):
		if isMockInstance( trackNode, 'AnimatorEventTrack' ):
			return TimelineEventTrackItem()
		else:
			return TimelineTrackItem()

	def onEditTool( self, toolName ):
		if toolName == 'add_key':
			self.owner.addKeyForSelectedTracks()

		elif toolName == 'remove_key':
			self.owner.removeSelectedKeys()

		elif toolName == 'clone_key':
			self.owner.cloneSelectedKeys()

		elif toolName == 'add_marker':
			self.owner.addMarker()

		super( AnimatorTimelineWidget, self ).onEditTool( toolName )

	def onTrackClicked( self, track, pos ):
		trackNode = track.node
		self.parentView.selectTrack( trackNode )
		
	def onKeyRemoving( self, keyNode ):
		return self.owner.onKeyRemoving( keyNode )

	def onMarkerRemoving( self, markerNode ):
		return self.owner.onMarkerRemoving( markerNode )

	def onClipRangeChanging( self, t0, t1 ):
		return self.owner.onClipLengthChanging( t1 )


##----------------------------------------------------------------##
class AnimatorClipTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		option['editable']           = False
		option['drag_mode']          = 'internal'
		option['multiple_selection'] = False
		option['show_root']          = True
		option['sorting']            = False
		super( AnimatorClipTreeWidget, self ).__init__( *args, **option )
		self.headerItem().setHidden( True )
		self.setAttribute(Qt.WA_MacShowFocusRect, False)
		self.setIndentation( 15 )

	def getHeaderInfo( self ):
		return [ ('Name',-1) ]

	def getRootNode( self ):
		return self.owner.getClipTreeRoot()

	def getNodeParent( self, node ):
		return node.parent

	def getNodeChildren( self, node ):
		return [ child for child in list(node.children.values()) ]

	def updateItemContent( self, item, node, **option ):
		item.setText( 0, node.toString( node ) )
		item.setIcon( 0, getIcon( node.getIcon( node ), 'animator_clip_tree_node' ) )

	def onItemSelectionChanged( self ):
		self.parentView.onTreeNodeSelectionChanged()


##----------------------------------------------------------------##
class AnimatorWidget( QtWidgets.QWidget, AnimatorWidgetUI ):
	"""docstring for AnimatorWidget"""
	def __init__( self, *args, **kwargs ):
		super(AnimatorWidget, self).__init__( *args, **kwargs )
		self.setupUi( self )

		self.treeTracks     = AnimatorTrackTree( parent = self )
		self.timeline       = AnimatorTimelineWidget( parent = self )
		self.filterClips    = GenericTreeFilter()
		self.treeClips      = AnimatorClipListTree( parent = self )
		self.treeClipTree   = AnimatorClipTreeWidget( parent = self )
		self.containerAnimTreeEditor.hide()
		self.propertyEditor = PropertyEditor( self )
		self.propertyEditor.propertyChanged.connect( self.onPropertyChanged )
		self.propertyEditor.objectChanged.connect( self.onPropertyTargetChanged )
		# self.treeTracks.setRowHeight( _TRACK_SIZE )

		self.treeTracks.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.treeTracks.verticalScrollBar().setStyleSheet('width:4px')
		self.treeTracks.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )

		self.toolbarTarget = QtWidgets.QToolBar()
		self.toolbarClips = QtWidgets.QToolBar()
		self.toolbarPlay  = QtWidgets.QToolBar()
		self.toolbarTrack = QtWidgets.QToolBar()
		self.toolbarClipTree = QtWidgets.QToolBar()
		self.toolbarEdit  = self.timeline.toolbarEdit

		self.timeline.toolbuttonCurveModeLinear   .setIcon( getIcon( 'curve_mode_linear'   ) )
		self.timeline.toolbuttonCurveModeConstant .setIcon( getIcon( 'curve_mode_constant' ) )
		self.timeline.toolbuttonCurveModeBezier   .setIcon( getIcon( 'curve_mode_bezier'   ) )
		self.timeline.toolbuttonCurveModeBezierS  .setIcon( getIcon( 'curve_mode_bezier_s' ) )

		self.timeline.toolbuttonAddMarker .setIcon( getIcon( 'marker' ) )
		self.timeline.toolbuttonAddKey    .setIcon( getIcon( 'add'    ) )
		self.timeline.toolbuttonRemoveKey .setIcon( getIcon( 'remove' ) )
		self.timeline.toolbuttonCloneKey  .setIcon( getIcon( 'clone'  ) )

		treeLayout = QtWidgets.QVBoxLayout(self.containerTree) 
		treeLayout.setSpacing( 0 )
		treeLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		treeLayout.addWidget( self.treeTracks )

		rightLayout = QtWidgets.QVBoxLayout(self.containerRight) 
		rightLayout.setSpacing( 0 )
		rightLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		rightLayout.addWidget( self.timeline )

		treeClipsLayout = QtWidgets.QVBoxLayout(self.containerClips) 
		treeClipsLayout.setSpacing( 0 )
		treeClipsLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		treeClipsLayout.addWidget( self.toolbarTarget )
		treeClipsLayout.addWidget( self.filterClips )
		self.filterClips.setTargetTree( self.treeClips )
		treeClipsLayout.addWidget( self.treeClips )
		treeClipsLayout.addWidget( self.toolbarClips )
		self.treeClips.setHeaderHidden( True )
		self.treeClips.verticalScrollBar().setStyleSheet('width:4px')

		treeClipTreeLayout = QtWidgets.QVBoxLayout(self.containerAnimTree) 
		treeClipTreeLayout.setSpacing( 0 )
		treeClipTreeLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		treeClipTreeLayout.addWidget( self.toolbarClipTree )
		treeClipTreeLayout.addWidget( self.treeClipTree )

		propLayout = QtWidgets.QVBoxLayout(self.containerProperty) 
		propLayout.setSpacing( 0 )
		propLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		propLayout.addWidget( self.propertyEditor )

		# headerHeight = self.treeTracks.header().height()
		playToolLayout = QtWidgets.QVBoxLayout(self.containerPlayTool) 
		playToolLayout.setSpacing( 0 )
		playToolLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		playToolLayout.addWidget( self.toolbarPlay )		
		playToolLayout.addStretch( )

		trackToolLayout = QtWidgets.QVBoxLayout(self.containerTrackTool) 
		trackToolLayout.setSpacing( 0 )
		trackToolLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		trackToolLayout.addWidget( self.toolbarTrack )		

		bottomToolHeight = 20
		self.containerTrackTool.setFixedHeight( bottomToolHeight )
		self.toolbarClips.setFixedHeight( bottomToolHeight )
		self.toolbarTrack.setFixedHeight( bottomToolHeight )
		
		topToolHeight = self.timeline.getRulerHeight()
		self.containerPlayTool.setFixedHeight( topToolHeight )
		self.toolbarPlay.setFixedHeight( topToolHeight )
		self.toolbarClipTree.setFixedHeight( topToolHeight )
		self.toolbarClips.setFixedHeight( topToolHeight )
		self.treeTracks.header().hide()

		self.treeTracks.setObjectName( 'AnimatorTrackTree' )
		self.treeClips.setObjectName( 'AnimatorClipListTree' )
		self.treeClipTree.setObjectName( 'AnimatorClipListTree' )
		self.toolbarPlay.setObjectName( 'TimelineToolBarPlay')
		self.toolbarTrack.setObjectName( 'TimelineToolBarTrack')

		#signals
		self.treeTracks.verticalScrollBar().valueChanged.connect( self.onTrackTreeScroll )
		self.timeline.cursorPosChanged.connect( self.onCursorPosChanged )
		self.timeline.trackView.scrollYChanged.connect( self.onTrackViewScrollDragged )
		self.treeTracks.layoutChanged.connect( self.updateTrackLayout )
		self.cursorMovable  = True
		self.updatingScroll = False

	def setOwner( self, owner ):
		self.owner = owner
		self.treeTracks.parentView = self
		self.treeClips.parentView = self
		self.timeline.parentView = self
		self.treeClipTree.parentView = self
		self.treeTracks.owner = owner
		self.treeClips.owner = owner
		self.timeline.owner = owner
		self.treeClipTree.owner = owner

		#signals
		self.timeline.markerChanged.connect( self.onMarkerChanged )
		self.timeline.keyChanged.connect( self.onKeyChanged )
		self.timeline.keyCurveValueChanged.connect( self.onKeyCurveValueChanged )
		self.timeline.keyBezierPointChanged.connect( self.onKeyBezierPointChanged )
		self.timeline.keyTweenModeChanged.connect( self.onKeyTweenModeChanged )


	def rebuild( self ):
		self.treeTracks.rebuild()
		self.treeClips.rebuild()
		self.timeline.rebuild()
		self.treeClipTree.rebuild()
		self.setTrackViewScrollRange( 0 )
		

	def rebuildTimeline( self ):
		self.timeline.rebuild()
		self.treeTracks.rebuild()

	def rebuildClipTree( self ):
		self.treeClipTree.rebuild()

	def rebuildClipList( self ):
		self.treeClips.rebuild()

	def updateTrackLayout( self ):
		self.timeline.updateTrackLayout()

	def createClip( self ):
		pass

	def addClip( self, clip, focus = False ):
		self.treeClips.addNode( clip )
		if focus:
			self.treeClips.selectNode( clip )
			self.treeClips.editNode( clip )

	def addKey( self, key, focus = False ):
		self.addTrack( key.parent )
		keyItem = self.timeline.addKey( key )
		if focus:
			self.timeline.selectKey( key )
		return keyItem

	def addClipTreeNode( self, node, focus = False ):
		self.treeClipTree.addNode( node )
		if focus:
			self.treeClipTree.selectNode( node )

	def addTrack( self, track, focus = False ):
		self.treeTracks.addNode( track )
		self.timeline.addTrack( track )
		if focus:
			self.treeTracks.editNode( track )
			self.timeline.setTrackSelection( [track] )

	def addMarker( self, marker, focus = False ):
		self.timeline.addMarker( marker )
		if focus:
			self.timeline.selectMarker( marker )

	def selectTrack( self, trackNode ):
		self.treeTracks.selectNode( trackNode )

	def removeClip( self, clip ):
		self.treeClips.removeNode( clip )

	def removeTrack( self, track ):
		self.treeTracks.removeNode( track )
		self.timeline.removeTrack( track )

	def removeKey( self, key ):
		self.timeline.removeKey( key )

	def removeMarker( self, marker ):
		self.timeline.removeMarker( marker )

	def setPropertyTarget( self, target ):
		self.propertyEditor.setTarget( target )

	def isTrackVisible( self, trackNode ):
		return self.treeTracks.isNodeVisible( trackNode )

	def getTrackPos( self, trackNode ):
		rect = self.treeTracks.getNodeVisualRect( trackNode )
		scrollY = self.treeTracks.verticalScrollBar().value()
		pos = rect.y() + 3 + scrollY
		return pos

	def onTrackViewScrollDragged( self, y ):
		if self.updatingScroll: return
		self.updatingScroll = True
		self.treeTracks.verticalScrollBar().setValue( -y )
		self.updatingScroll = False

	def setTrackViewScrollRange( self, maxRange ):
		self.timeline.setTrackViewScrollRange( maxRange )

	def onTrackTreeScroll( self, v ):
		self.timeline.setTrackViewScroll( -v )

	def onTrackFolded( self, track, folded ):
		track._folded = folded
		self.timeline.updateTrackLayout()
		self.timeline.clearSelection()

	def onMarkerChanged( self, marker, pos ):
		self.propertyEditor.refreshFor( marker )
		self.owner.onTimelineMarkerChanged( marker, pos )

	def onKeyChanged( self, key, pos, length ):
		self.propertyEditor.refreshFor( key )
		self.owner.onTimelineKeyChanged( key, pos, length )

	def onKeyCurveValueChanged( self, key, value ):
		self.owner.onTimelineKeyCurveValueChanged( key, value )

	def onKeyBezierPointChanged( self, key, bpx0, bpy0, bpx1, bpy1 ):
		self.owner.onTimelineKeyBezierPointChanged( key, bpx0, bpy0, bpx1, bpy1 )

	def onKeyTweenModeChanged( self, key, mode ):
		if mode == TWEEN_MODE_LINEAR:
			mode = 0
		elif mode == TWEEN_MODE_CONSTANT:
			mode = 1
		elif mode == TWEEN_MODE_BEZIER:
			mode = 2
		else:
			mode = 0
		self.owner.onTimelineKeyTweenModeChanged( key, mode )

	def onPropertyChanged( self, obj, fid, value ):
		pass
		# if isMockInstance( obj, 'AnimatorKey' ):
		# 	self.timelin
		# 	if fid == 'pos' or fid == 'length':
		# 		self.timeline.refreshKey( obj )
		# elif isMockInstance( obj, 'AnimatorClipMarker' ):
		# 	if fid == 'name' or fid =='pos':
		# 		self.timeline.refreshMarker( obj )
		# self.owner.onObjectEdited( obj )

	def onPropertyTargetChanged( self, obj ):
		if isMockInstance( obj, 'AnimatorKey' ):
				obj.updateDependecy( obj )
				self.timeline.refreshKey( obj )
		elif isMockInstance( obj, 'AnimatorClipMarker' ):
				self.timeline.refreshMarker( obj )
		elif isMockInstance( obj, 'AnimatorClipTreeNode' ):
			self.treeClipTree.refreshNodeContent( obj )
		self.owner.onObjectEdited( obj )

	def setEnabled( self, enabled ):
		super( AnimatorWidget, self ).setEnabled( enabled )
		self.timeline.setEnabled( enabled )

	def startPreview( self ):
		# self.timeline.setCursorDraggable( False )
		pass

	def stopPreview( self ):
		# self.timeline.setCursorDraggable( True )
		pass

	def setCursorMovable( self, movable ):
		self.cursorMovable = movable
		self.timeline.setCursorDraggable( movable )		

	def onCursorPosChanged( self, pos ):
		if self.cursorMovable:
			self.owner.applyTime( pos )

	def setCursorPos( self, pos, focus = False ):
		self.timeline.setCursorPos( pos, focus )

	def getCursorPos( self ):
		return self.timeline.getCursorPos()

	def onTrackSelectioChanged( self ):
		selection = self.treeTracks.getSelection()
		self.timeline.setTrackSelection( selection )
		if selection:
			track = selection[0]
		else:
			track = None
		self.owner.setCurrentTrack( track )
		
	def onClipSelectioChanged( self ):
		selection = self.treeClips.getSelection()
		if selection:
			clip = selection[0]
		else:
			clip = None
		
		self.setPropertyTarget( None )

		if isMockInstance( clip, 'AnimatorClipTree' ):
			self.containerTimelineEditor.hide()
			self.containerAnimTreeEditor.show()
			self.owner.setTargetClip( clip )
			self.timeline.setCursorPos( 0 )
			self.owner.applyTime( 0 )

		elif isMockInstance( clip, 'AnimatorClip' ):
			self.containerTimelineEditor.show()
			self.containerAnimTreeEditor.hide()
			self.owner.setTargetClip( clip )
			self.timeline.setCursorPos( 0 )
			self.owner.applyTime( 0 )

		elif isMockInstance( clip, 'AnimatorClipGroup' ):
			self.owner.setTargetClip( None )
			
		else:
			#TODO
			pass

	def onTreeNodeSelectionChanged( self ):
		for node in self.treeClipTree.getSelection():
			self.setPropertyTarget( node )
			return

	def getTrackSelection( self ):
		return self.timeline.getTrackSelection()

	def getClipSelection( self ):
		return self.treeClips.getSelection()

	def getKeySelection( self ):
		return self.timeline.getSelection()

	def getClipTreeNodeSelection( self ):
		return self.treeClipTree.getSelection()

	def getCurrentClipGroup( self ):
		selection = self.treeClips.getSelection()
		if selection:
			node = selection[ 0 ]
			while node:
				if isMockInstance( node, 'AnimatorClipGroup' ):
					return node
				node = node.parentGroup
		return None

	def getCurrentClipRange( self ):
		selection = self.treeClips.getSelection()
		if selection:
			node = selection[ 0 ]
			fixedLength = node.fixedLength
			return ( 0, fixedLength )
	

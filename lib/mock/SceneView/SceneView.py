import subprocess
import os
import os.path
import shutil
import time
import json

from gii.core         import *
from gii.qt           import *
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.helpers    import addWidgetWithLayout, restrainWidgetToScreen
from gii.qt.IconCache import getIcon
from gii.qt.dialogs   import requestString, alertMessage, requestColor

from gii.SceneEditor  import SceneEditorModule, SceneTool, SceneToolMeta, SceneToolButton
from gii.qt.controls.GenericTreeWidget  import GenericTreeWidget, GenericTreeFilter

from mock import  MOCKEditCanvas

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt, Signal
from qtpy.QtCore import QEventLoop, QEvent, QObject


from mock import _MOCK, isMockInstance

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class SceneViewTool( SceneTool ):
	context = 'scene_view'
	cursor  = 'arrow'

	def getSceneViewToolId( self ):
		toolId = getattr( self.__class__, 'tool' )
		if not toolId:
			raise Exception( 'no scene view tool Id specified' )
		return toolId

	def start( self, **context ):
		canvasToolId = self.getSceneViewToolId()
		view = app.getModule( 'scene_view' )
		view.changeCanvasTool( canvasToolId )
		view.canvas.setCursorByName( self.cursor )
		self.onStart( **context )
	
	def onStart( self, **context ):
		pass


##----------------------------------------------------------------##
class SceneViewToolSelection( SceneViewTool ):
	name     = 'scene_view_selection'
	shortcut = 'Q'
	tool     = 'selection'

##----------------------------------------------------------------##
class SceneViewToolTranslation( SceneViewTool ):
	name     = 'scene_view_translation'
	shortcut = 'W'
	tool     = 'translation'

##----------------------------------------------------------------##
class SceneViewToolRotation( SceneViewTool ):
	name     = 'scene_view_rotation'
	shortcut = 'E'
	tool     = 'rotation'

##----------------------------------------------------------------##
class SceneViewToolScale( SceneViewTool ):
	name     = 'scene_view_scale'
	shortcut = 'R'
	tool     = 'scale'

##----------------------------------------------------------------##
class SceneViewToolManipulator( SceneViewTool ):
	name     = 'scene_view_manipulator'
	shortcut = 'T'
	tool     = 'manipulator'

##----------------------------------------------------------------##
class SceneView( SceneEditorModule ):
	name       = 'scene_view'
	dependency = [ 'mock', 'scene_editor', 'scenegraph_editor' ]

	def onLoad( self ):
		self.targetSceneNode = None
		self.targetScene = None
		self.previousDragData = None

		self.window = self.requestDocumentWindow(
				title = 'Scene',
				icon  = 'scene'
			)

		self.gizmoManagerWidget = None
		self.toolbar = self.window.addToolBar()
		self.toolbar.setFixedHeight( 24 )
		self.toolbar.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
		)
		self.addToolBar( 'scene_view_config', self.toolbar )


		self.canvasFrame = self.window.addWidget( SceneViewCanvasFrame() )
		self.canvas = self.canvasFrame.canvas

		self.canvas.loadScript( _getModulePath('SceneViewScript.lua') )
		self.canvas.parentView = self
		
		self.canvas.setDelegateEnv( '_giiSceneView', self )

		##----------------------------------------------------------------##
		self.sceneInfoBox = self.window.addWidget( QtWidgets.QLabel() )
		self.sceneInfoBox.setSizePolicy(
				QtWidgets.QSizePolicy.Expanding,
				QtWidgets.QSizePolicy.Fixed
			)
		self.sceneInfoBox.setMinimumSize( 10, 18 )
		self.sceneInfoBox.setContentsMargins( 10,0,0,0 )

		self.updateTimer        = None
		self.updatePending      = False
		self.previewing         = False
		self.previewUpdateTimer = False

		signals.connect( 'entity.modified',       self.onEntityModified   )
		signals.connect( 'entity.gizmo_changed',  self.onEntityGizmoChanged )
		signals.connect( 'asset.post_import_all', self.onAssetReimport    )
		signals.connect( 'scene.open',            self.onSceneOpen        )
		signals.connect( 'scene.close',           self.onSceneClose       )
		signals.connect( 'scene.change',          self.onSceneUpdate      )
		signals.connect( 'scene.update',          self.onSceneUpdate      )
		signals.connect( 'selection.changed',     self.onSelectionChanged )

		signals.connect( 'animator.start', self.onAnimatorStart )
		signals.connect( 'animator.stop',  self.onAnimatorStop )

		signals.connect( 'preview.resume', self.onPreviewResume )
		signals.connect( 'preview.pause',  self.onPreviewStop   )
		signals.connect( 'preview.stop',   self.onPreviewStop   )

		signals.connect( 'script.reload',  self.onScriptReload )

		##----------------------------------------------------------------##
		self.addShortcut( 'scene_view', 'F',  'scene_editor/focus_selection' )
		self.addShortcut( 'scene_view', '/',  self.toggleDebugLines )
		self.addShortcut( 'scene_view', 'ctrl+;',  self.toggleRootGizmoVisibility )

		self.addShortcut( self.canvas, 'Delete', 'scene_editor/remove_entity' )
		self.addShortcut( self.canvas, 'Backspace', 'scene_editor/remove_entity' )
		self.addShortcut( self.canvas, 'ctrl+/', 'scene_editor/toggle_entity_visibility' )
		
		self.addShortcut( self.canvas, 'ctrl+x', self.cutEntityToClipboard )
		self.addShortcut( self.canvas, 'ctrl+c', self.copyEntityToClipboard )
		self.addShortcut( self.canvas, 'ctrl+v', self.pasteEntityFromClipboard, 'sibling' )
		self.addShortcut( self.canvas, 'ctrl+alt+v', self.pasteEntityFromClipboard, 'into' )

		self.addShortcut( self.canvas, 'Escape', self.clearSelection )


		##----------------------------------------------------------------##
		self.mainToolBar = self.addToolBar( 'scene_view_tools', 
			self.getMainWindow().requestToolBar( 'view_tools' )
			)

		self.addTool(	'scene_view_tools/tool_selection',
			widget = SceneToolButton( 'scene_view_selection',
				icon = 'tools/selection',
				label = 'Selection'
				)
			)

		self.addTool(	'scene_view_tools/tool_translation',
			widget = SceneToolButton( 'scene_view_translation',
				icon = 'tools/translation',
				label = 'Translation'
				)
			)

		self.addTool(	'scene_view_tools/tool_rotation',
			widget = SceneToolButton( 'scene_view_rotation',
				icon = 'tools/rotation',
				label = 'Rotation'
				)
			)

		self.addTool(	'scene_view_tools/tool_scale',
			widget = SceneToolButton( 'scene_view_scale',
				icon = 'tools/scale',
				label = 'Scale'
				)
			)

		self.addTool(	'scene_view_tools/----' )
		
		self.addTool(	'scene_view_tools/tool_manipulator',
			widget = SceneToolButton( 'scene_view_manipulator',
				icon = 'tools/manipulator',
				label = 'Manipulator'
			)
		)

		# ##----------------------------------------------------------------##
		# self.alignToolBar = self.addToolBar( 'scene_view_tools_align', 
		# 	self.getMainWindow().requestToolBar( 'view_tools_align' )
		# 	)

		# self.addTool(	'scene_view_tools_align/align_bottom',
		# 	label = 'Align Bottom',
		# 	icon  = 'tools/align-bottom-edges',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'align_bottom' ),
		# )

		# self.addTool(	'scene_view_tools_align/align_top',
		# 	label = 'Align Top',
		# 	icon  = 'tools/align-top-edges',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'align_top' ),
		# )

		# self.addTool(	'scene_view_tools_align/align_vcenter',
		# 	label = 'Align V Center',
		# 	icon  = 'tools/align-vertical-centers',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'align_vcenter' ),
		# )

		# self.addTool(	'scene_view_tools_align/align_left',
		# 	label = 'Align Left',
		# 	icon  = 'tools/align-left-edges',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'align_left' ),
		# )

		# self.addTool(	'scene_view_tools_align/align_right',
		# 	label = 'Align Right',
		# 	icon  = 'tools/align-right-edges',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'align_right' ),
		# )

		# self.addTool(	'scene_view_tools_align/align_hcenter',
		# 	label = 'Align H Center',
		# 	icon  = 'tools/align-horizontal-centers',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'align_hcenter' ),
		# )

		# self.addTool(	'scene_view_tools_align/----' )

		# self.addTool(	'scene_view_tools_align/push_together_left',
		# 	label = 'Push Left',
		# 	icon  = 'tools/push-together-left',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'push_together_left' ),
		# )

		# self.addTool(	'scene_view_tools_align/push_together_right',
		# 	label = 'Push right',
		# 	icon  = 'tools/push-together-right',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'push_together_right' ),
		# )

		# self.addTool(	'scene_view_tools_align/push_together_top',
		# 	label = 'Push top',
		# 	icon  = 'tools/push-together-top',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'push_together_top' ),
		# )

		# self.addTool(	'scene_view_tools_align/push_together_bottom',
		# 	label = 'Push bottom',
		# 	icon  = 'tools/push-together-bottom',
		# 	command   = 'align_entities',
		# 	command_args = dict( mode = 'push_together_bottom' ),
		# )

		#config tool
		self.addTool(	'scene_view_config/copy_url', 
			label = 'get URL',
			icon  = '@',
		)
		
		self.addTool(	'scene_view_config/----' ) 

		self.addTool(	'scene_view_config/copy_framebuffer', 
			label = 'Copy Framebuffer',
			icon  = 'clipboard',
		)

		self.addTool(	'scene_view_config/locate_scene_asset', 
			label = 'Locate Scene Asset',
			icon  = 'search',
		)

		self.addTool(	'scene_view_config/----' )


		self.addTool(	'scene_view_config/gizmo_visible_manager', 
			label = 'Gizmo',
			icon  = 'gizmo-all',
		)

		self.addTool(	'scene_view_config/toggle_snap_grid', 
			label = 'snap',
			icon  = 'magnet',
			type  = 'check'
			)

		self.addTool(	'scene_view_config/toggle_grid', 
			label = 'grid',
			icon  = 'grid',
			type  = 'check'
			)

		self.gridWidthSpinBox = QtWidgets.QSpinBox()
		self.gridWidthSpinBox.setRange( 10, 1000 )
		self.gridWidthSpinBox.valueChanged.connect( self.onGridWidthChange )
		self.gridWidthSpinBox.setButtonSymbols( QtWidgets.QAbstractSpinBox.NoButtons )
		self.toolbar.addWidget( self.gridWidthSpinBox )

		self.gridHeightSpinBox = QtWidgets.QSpinBox()
		self.gridHeightSpinBox.setRange( 10, 1000 )
		self.gridHeightSpinBox.valueChanged.connect( self.onGridHeightChange )
		self.gridHeightSpinBox.setButtonSymbols( QtWidgets.QAbstractSpinBox.NoButtons )
		self.toolbar.addWidget( self.gridHeightSpinBox )
		
		self.toolbar.addSeparator()
		self.cursorInfoBox = CursorInfoBox()
		self.cursorInfoBox.parentView = self
		self.toolbar.addWidget( self.cursorInfoBox )
		self.cursorInfoBox.setMousePos( 0, 0 )
		self.cursorInfoBox.setZoom( 1 )
		self.cursorInfoBox.show()


	def onStart( self ):
		self.scheduleUpdate()
		self.updateTimer = self.window.startTimer( 60, self.onUpdateTimer )
		self.updateTimer.stop()
		self.updateTimer.timeout.connect( self.onUpdateTimer )

	def getModuleWindow( self ):
		return self.canvas

	def changeCanvasTool( self, name ):
		self.canvas.makeCurrentCanvas()
		self.canvas.safeCallMethod( 'view', 'changeCanvasTool', name )

	def toggleDebugLines( self ):
		self.canvas.makeCurrentCanvas()
		self.canvas.safeCallMethod( 'view', 'toggleDebugLines' )

	def onUpdateTimer( self ):
		if not self.updatePending == True: return
		self.updatePending = False
		if not self.previewing:
			self.getModule( 'game_preview' ).refresh()
		self.canvas.makeCurrentCanvas()
		self.canvas.callMethod( 'view', 'updateCanvas', True, self.previewing )
			
	def onSetFocus( self ):
		self.getModule( 'scene_editor' ).setFocus()
		self.window.show()
		self.window.setFocus()

	def onEntityModified( self, entity, context = None ):
		self.scheduleUpdate()

	def onEntityGizmoChanged( self, entity, context = None ):
		self.canvas.safeCallMethod( 'view', 'refreshGizmo' )
		self.scheduleUpdate()

	def onAssetReimport( self ):
		self.scheduleUpdate()

	def onSceneUpdate( self ):
		self.scheduleUpdate()

	def onSceneOpen( self, node, scene ):
		self.targetSceneNode = node
		self.targetScene = scene

		self.window.setWindowTitle( node.getPath() )
		# self.window.setDocumentName( node.getPath() )
		self.canvas.show()
		self.toolbar.show()
		self.canvas.safeCall( 'onSceneOpen', scene )
		self.loadWorkspaceState()
		self.canvas.refreshSize()
		self.setFocus()
		self.updateTimer.start()
		self.scheduleUpdate()

		#sync toolbar
		gridWidth   = self.canvas.callMethod( 'view', 'getGridWidth'  )
		gridHeight  = self.canvas.callMethod( 'view', 'getGridHeight' )
		gridVisible = self.canvas.callMethod( 'view', 'isGridVisible' )
		gridSnapping = self.canvas.callMethod( 'view', 'isGridSnapping' )
		gizmoVisible = self.canvas.callMethod( 'view', 'isGizmoVisible' )
		self.gridWidthSpinBox.setValue(	gridWidth	)
		self.gridHeightSpinBox.setValue( gridHeight )
		self.findTool( 'scene_view_config/toggle_grid' ).setValue( gridVisible )
		self.findTool( 'scene_view_config/toggle_snap_grid' ).setValue( gridSnapping )
		# self.findTool( 'scene_view_config/toggle_gizmo_visible' ).setValue( gizmoVisible )
		self.getModule( 'scene_tool_manager' ).changeTool( 'scene_view_translation' )
		self.getModule( 'game_preview' ).refresh()

	def makeCanvasCurrent( self ):
		self.canvas.makeCurrentCanvas()

	def onSceneClose( self, node ):
		self.saveWorkspaceState()
		self.targetSceneNode = None
		self.targetScene = None

		self.window.setDocumentName( None )
		# self.makeCanvasCurrent()
		self.canvas.safeCall( 'onSceneClose' )
		self.canvas.hide()
		self.toolbar.hide()
		self.updateTimer.stop()
		self.getModule( 'game_preview' ).refresh()

	def onSelectionChanged( self, selection, key ):
		if key != 'scene': return
		self.canvas.safeCallMethod( 'view', 'onSelectionChanged', selection )

	def loadWorkspaceState( self ):
		if not self.targetSceneNode: return
		dataString = self.targetSceneNode.getWorkspaceData( 'scene_view', None )
		self.canvas.callMethod( 'view', 'loadWorkspaceStateFromString', dataString )

	def saveWorkspaceState( self ):
		if not self.targetSceneNode: return
		dataString = self.canvas.callMethod( 'view', 'saveWorkspaceStateToString' )
		self.targetSceneNode.setWorkspaceData( 'scene_view', dataString or '' )

	def loadCameraState( self, cameraStateString ):
		if not self.targetSceneNode: return
		self.canvas.callMethod( 'view', 'loadCameraStateFromString', cameraStateString )


	def updateInPreview( self ):
		self.scheduleUpdate()
		introspector = self.getModule('introspector')
		if introspector:
			introspector.refresh()

	def setCameraZoom( self, zoom ):
		if not self.targetScene: return
		if isinstance( zoom, (float, int ) ) and zoom > 0:
			self.canvas.delegate.callMethod( 'view', 'setCameraZoom', zoom )

	def updateMouseLoc( self, x, y ):
		if not self.targetScene: return
		x,y,z  = self.canvas.delegate.callMethod( 'view', 'wndToWorld', x, y, 0 )
		self.cursorInfoBox.setMousePos( x, y )

	def updateCameraZoom( self ):
		if not self.targetScene: return
		zoom = self.canvas.callMethod( 'view', 'getCameraZoom' )
		self.cursorInfoBox.setZoom( zoom or 0 )

	def onPreviewResume( self ):
		self.previewing = True
		self.toolbar.setStyleSheet('QToolBar{ border-bottom: 1px solid rgb(0, 120, 0); }')
		self.previewUpdateTimer = self.window.startTimer( 1, self.updateInPreview )

	def onPreviewStop( self ):
		self.previewing = False
		self.toolbar.setStyleSheet('QToolBar{ border-bottom: none }')
		self.previewUpdateTimer.stop()

	def onAnimatorStart( self ):
		self.toolbar.setStyleSheet('QToolBar{ border-bottom: 1px solid rgb(255, 0, 120); }')
		self.animating = True

	def onAnimatorStop( self ):
		self.toolbar.setStyleSheet('QToolBar{ border-bottom: none }')
		self.animating = True

	def scheduleUpdate( self ):
		self.updatePending = True

	def forceUpdate( self ):
		self.scheduleUpdate()
		self.onUpdateTimer()

	def focusSelection( self ):
		self.canvas.safeCallMethod( 'view', 'focusSelection' )

	def onTool( self, tool ):
		name = tool.name
		if name == 'toggle_grid':
			self.canvas.safeCallMethod( 'view', 'setGridVisible', tool.getValue() )
			self.scheduleUpdate()

		elif name == 'toggle_snap_grid':
			self.canvas.safeCallMethod( 'view', 'setGridSnapping', tool.getValue() )
			self.scheduleUpdate()

		elif name == 'toggle_gizmo_visible':
			self.canvas.safeCallMethod( 'view', 'setGizmoVisible', tool.getValue() )
			self.scheduleUpdate()

		elif name == 'locate_scene_asset':
			sceneGraphEditor = self.getModule( 'scenegraph_editor')
			if sceneGraphEditor.activeSceneNode:
				assetBrowser = self.getModule( 'asset_browser' )
				if assetBrowser:
					assetBrowser.locateAsset( sceneGraphEditor.activeSceneNode )

		elif name == 'gizmo_visible_manager':
			self.openGizmoManager()

		elif name == 'copy_framebuffer':
			self.copyFramebuffer()

		elif name == 'copy_url':
			self.copyURL()

	def copyFramebuffer( self, withAlpha = False ):
		image = self.canvas.grabFramebuffer()
		if image:
			clipboard = QtWidgets.QApplication.clipboard()
			clipboard.setImage( image )

	def copyURL( self ):
		if not self.targetSceneNode:
			return
		cameraState = self.canvas.callMethod( 'view', 'saveCameraStateToString' )
		path = self.targetSceneNode.getPath()
		url = self.getApp().makeURL( 'scene', path = path, camera = cameraState )
		#TODO: position
		mime = QtCore.QMimeData()
		mime.setUrls( [ QtCore.QUrl( url ) ] )
		mime.setText( url )
		clipboard = QtWidgets.QApplication.clipboard()
		clipboard.setMimeData( mime )

	def getCurrentSceneView( self ):
		#TODO
		return self

	def openGizmoManager( self ):
		if not self.gizmoManagerWidget:
			self.gizmoManagerWidget = GizmoVisiblityManagerWidget()
			self.gizmoManagerWidget.setParentView( self )
		self.gizmoManagerWidget.start()

	def getGizmoVisiblityTreeRoot( self ):
		gizmoManager = self.canvas.getDelegateEnv( 'view' ).gizmoManager
		return gizmoManager.getVisiblityTreeRoot( gizmoManager )


	def toggleRootGizmoVisibility( self ):
		root = self.getGizmoVisiblityTreeRoot()
		return self.toggleGizmoVisibility( root )

	def toggleGizmoVisibility( self, visEntry ):
		visEntry.toggle( visEntry )
		self.canvas.safeCallMethod( 'view', 'updateGizmoVisibility' )
		if self.gizmoManagerWidget:
			self.gizmoManagerWidget.tree.refreshNodeContent( visEntry, updateChildren = True )
		self.canvas.updateCanvas()

	def resetGizmoVisibility( self ):
		self.canvas.safeCallMethod( 'view', 'resetGizmoVisibility' )
		self.canvas.updateCanvas()

	def clearSelection( self ):
		self.changeSelection( None )

	def copyEntityToClipboard( self ):
		self.getModule( 'scenegraph_editor' ).copyEntityToClipboard()

	def cutEntityToClipboard( self ):
		self.getModule( 'scenegraph_editor' ).cutEntityToClipboard()

	def pasteEntityFromClipboard( self, pos ):
		self.getModule( 'scenegraph_editor' ).pasteEntityFromClipboard( pos )

	def onScriptReload( self ):
		#refresh gizmo list?
		pass

	def onDragStart( self, mimeType, data, x, y ):
		if self.previousDragData == data: return True
		self.canvas.refreshModifiers()
		accepted = self.canvas.callMethod( 'view', 'startDrag', mimeType, data, x, y )
		if accepted:
			self.previousDragData = data
			return True
		else:
			self.previousDragData = None
			return False

	def onDragMove( self, x, y ):
		self.canvas.callMethod( 'view', 'moveDrag', x, y )

	def onDragDrop( self, x, y ):
		self.canvas.callMethod( 'view', 'finishDrag', x, y )
		self.previousDragData = None

	def onDragLeave( self ):
		self.canvas.callMethod( 'view', 'stopDrag' )
		self.previousDragData = None

	def onGridWidthChange( self, v ):
		self.canvas.safeCallMethod( 'view', 'setGridWidth', v )
		self.scheduleUpdate()

	def onGridHeightChange( self, v ):
		self.canvas.safeCallMethod( 'view', 'setGridHeight', v )
		self.scheduleUpdate()


	def disableCamera( self ):
		self.canvas.callMethod( 'view', 'disableCamera' )

	def enableCamera( self ):
		self.canvas.callMethod( 'view', 'disableCamera' )

	def hideEditorLayer( self ):
		self.canvas.callMethod( 'view', 'hideEditorLayer' )

	def showEditorLayer( self ):
		self.canvas.callMethod( 'view', 'showEditorLayer' )

	def setInfo( self, text ):
		self.sceneInfoBox.setText( text )


##----------------------------------------------------------------##
class SceneViewCanvasFrame( QtWidgets.QFrame ):
	def __init__( self, *args ):
		super( SceneViewCanvasFrame, self ).__init__( *args )
		layout = QtWidgets.QVBoxLayout()
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		self.setLayout( layout )
		self.canvas = SceneViewCanvas( self, context_prefix = 'scene_view' )
		layout.addWidget( self.canvas )

##----------------------------------------------------------------##
class SceneViewCanvas( MOCKEditCanvas ):
	def __init__( self, *args, **kwargs ):
		super( SceneViewCanvas, self ).__init__( *args, **kwargs )
		self.parentView = None
		self.setAcceptDrops( True )		
		self.setTabletTracking( True )

	def dragEnterEvent( self, event ):
		mimeData = event.mimeData()
		pos = event.pos()
		ratio = self.pixelRatio
		x,y=pos.x() * ratio, pos.y() * ratio
		accepted = False
		if mimeData.hasFormat( GII_MIME_ASSET_LIST ):
			if self.parentView.onDragStart(
				GII_MIME_ASSET_LIST, str( mimeData.data( GII_MIME_ASSET_LIST ), 'utf-8' ),
				x, y
				):
				accepted = True
		if accepted:
			event.acceptProposedAction()

	def dragMoveEvent( self, event ):
		ratio = self.pixelRatio
		pos = event.pos()
		x,y=pos.x() * ratio, pos.y() * ratio
		self.parentView.onDragMove( x, y )
		event.acceptProposedAction()

	def dragLeaveEvent( self, event ):
		self.parentView.onDragLeave()

	def dropEvent( self, event ):
		# pos = event.pos()
		ratio = self.pixelRatio
		pos = event.pos()
		x,y=pos.x() * ratio, pos.y() * ratio
		self.parentView.onDragDrop( x, y )
		event.acceptProposedAction()
		self.setFocus()

	def enterEvent(self, event):
		super( SceneViewCanvas, self ).enterEvent( event )
		self.setFocus()

	def mouseMoveEvent( self, event ):
		if self.parentView:
			ratio = self.pixelRatio
			x,y=event.x() * ratio, event.y() * ratio
			if not event.buttons():
				self.parentView.updateMouseLoc( x, y )
			# if not ( event.buttons() & Qt.MiddleButton ):
			# 	self.parentView.updateMouseLoc( x, y )
		return super( SceneViewCanvas, self ).mouseMoveEvent( event )

	def updateCanvas( self, **option ):
		if self.parentView:
			self.parentView.updateCameraZoom()
		# option['no_sim'] = False
		super( SceneViewCanvas, self ).updateCanvas( **option )


##----------------------------------------------------------------##
class GizmoVisiblityManagerWidget( QtWidgets.QWidget ):
	def __init__( self, *args ):
		super( GizmoVisiblityManagerWidget, self ).__init__( *args )
		self.setWindowFlags( Qt.Window | Qt.FramelessWindowHint )
		# self.setWindowModality( Qt.ApplicationModal )
		
		layout = QtWidgets.QVBoxLayout( self )
		layout.setContentsMargins( 5 , 5 , 5 , 5 )
		layout.setSpacing( 5 )
		self.buttonReset = QtWidgets.QToolButton( self )
		self.buttonReset.setText( 'Reset All' )
		self.buttonReset.clicked.connect( self.onButtonReset )
		self.treeFilter = GenericTreeFilter( self )
		self.tree = GizmoVisiblityTreeWidget( self )
		label = QtWidgets.QLabel( self )
		label.setText( 'Gizmo Visiblity:')
		layout.addWidget( label )
		layout.addWidget( self.buttonReset )
		layout.addWidget( self.treeFilter )
		layout.addWidget( self.tree )
		self.treeFilter.setTargetTree( self.tree )
		self.setMinimumSize( 250, 400 )
		self.setMaximumWidth( 250 )

	def onButtonReset( self ):
		self.view.resetGizmoVisibility()
		self.tree.refreshNodeContent( self.tree.getRootNode(), updateChildren = True )

	def setParentView( self, view ):
		self.view = view
		self.tree.view = view

	def start( self ):
		pos        = QtGui.QCursor.pos()
		self.move( pos )
		restrainWidgetToScreen( self )
		self.tree.rebuild()
		self.show()
		self.raise_()
		self.tree.setFocus()
		#fit size

	def event( self, ev ):
		e = ev.type()		
		if e == QEvent.KeyPress and ev.key() == Qt.Key_Escape:
			self.hide()
			self.view.setFocus()
			
		elif e == QEvent.WindowDeactivate:
			self.hide()
			self.view.setFocus()

		return super( GizmoVisiblityManagerWidget, self ).event( ev )

##----------------------------------------------------------------##
class GizmoVisiblityTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		# option[ 'sorting' ] = False
		option[ 'show_root' ] = True
		super( GizmoVisiblityTreeWidget, self ).__init__( *args, **option )
		self.setAttribute(Qt.WA_MacShowFocusRect, False)

	def getHeaderInfo( self ):
		return [('Name',175), ('Show',30 ) ]

	def getRootNode( self ):
		return self.view.getGizmoVisiblityTreeRoot()

	def getNodeParent( self, node ): # reimplemnt for target node	
		return node.parent

	def getNodeChildren( self, node ):
		groups = []
		entries = []
		for entry in list(node.children.values()):
			if isMockInstance( entry, 'GizmoVisibilityGroup' ):
				groups.append( entry )
			else:
				entries.append( entry )
		return groups + entries

	def compareNodes( self, node1, node2 ):
		return node1._priority >= node2._priority

	def updateItemContent( self, item, node, **option ):
		name = None
		item.setData( 0, Qt.UserRole, 0 )
		item.setText( 0, node.getLabel( node ) )

		if node.isVisible( node ):
			item.setIcon( 1, getIcon( 'entity_vis' ) )
		elif node.isLocalVisible( node ):
			item.setIcon( 1, getIcon( 'entity_parent_invis' ) )
		else:
			item.setIcon( 1, getIcon( 'entity_invis' ) )

	def mousePressEvent( self, event ):
		if event.button() == Qt.LeftButton:
			item = self.itemAt( event.pos() )
			if item:
				col = self.columnAt( event.pos().x() )
				if col == 1:
					node = self.getNodeByItem( item )
					self.view.toggleGizmoVisibility( node )
					return
			
		return super( GizmoVisiblityTreeWidget, self ).mousePressEvent( event )


##----------------------------------------------------------------##
class CursorInfoBox( QtWidgets.QWidget ):
	"""docstring for CursorInfoBox`"""
	def __init__(self, *args):
		super(CursorInfoBox, self).__init__( *args )
		self.textZoom = QtWidgets.QDoubleSpinBox( self )
		self.textZoom.setDecimals( 1 )
		self.textZoom.setMaximum( 10000 )
		self.textZoom.setMinimum( 0.001 )
		self.textPos  = QtWidgets.QLabel( self )
		self.textPos.setObjectName( 'TextPos' )
		self.textZoom.setFixedWidth( 60 )
		self.textPos.setFixedWidth( 120 )
		self.buttonResetZoom = QtWidgets.QToolButton( self )
		self.buttonResetZoom.setFixedSize( 20, 20 )
		self.buttonResetZoom.setIcon( getIcon( 'reset' ) )
		self.buttonResetZoom.clicked.connect( self.resetZoom )
		layout = QtWidgets.QHBoxLayout( self )
		layout.addWidget( self.textZoom )
		layout.addWidget( self.buttonResetZoom )
		layout.addWidget( self.textPos )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		self.textZoom.valueChanged.connect( self.onZoomChanged )
		self.setFixedHeight( 24 )
		self.parentView = None

		self.refreshTimer = QtCore.QTimer( self )
		self.refreshTimer.setTimerType( Qt.PreciseTimer )
		self.refreshTimer.setSingleShot( True )
		self.refreshTimer.timeout.connect( self.doRefresh )
		self.refreshTimer.setInterval( 0.1 )

		self.mousePos = ( 0, 0 )
		self.cameraZoom = 1

	def setZoom( self, zoom ):
		if self.cameraZoom == zoom: return
		self.cameraZoom = zoom
		self.refreshTimer.start()

	def resetZoom( self ):
		self.textZoom.setValue( 100 )

	def setMousePos( self, x, y ):
		self.mousePos = ( x, y )
		self.refreshTimer.start()

	def onZoomChanged( self, z ):
		if self.parentView:
			self.parentView.setCameraZoom( z/100.0 )

	def doRefresh( self ):
		self.setUpdatesEnabled( False )
		self.blockSignals( True )

		x, y = self.mousePos
		self.textPos.setText( '(%.1f, %.1f)' % ( x, y ) )
		self.textZoom.setValue( self.cameraZoom * 100 )

		self.blockSignals( False )
		self.setUpdatesEnabled( True )


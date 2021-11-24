import os.path
import time
import logging

from gii.core                import signals, app, RemoteCommand

from gii.moai.MOAIRuntime    import getAKU
from gii.moai.MOAICanvasBase import MOAICanvasBase
from gii.moai.MOAIEditCanvas import MOAIEditCanvas

from gii.qt.dialogs          import ProcessDialog, alertMessage

from qtpy                   import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore            import Qt

from .SceneEditor             import SceneEditorModule
from . import ExternRun

##----------------------------------------------------------------##
class GamePreview( SceneEditorModule ):
	"""docstring for GamePreview"""

	def __init__(self):
		super(GamePreview, self).__init__()
		self.paused         = False
		self.waitActivate   = False
		self.viewWidth      = 0
		self.viewHeight     = 0
		self.pendingScript  = None
		self.activeFPS      = 60
		self.nonActiveFPS   = 30
		self.previewCanvasClasPriority = -1000
		self.previewCanvasClas = None

	def getName(self):
		return 'game_preview'

	def getDependency(self):
		return [ 'qt', 'moai', 'scene_editor' ]

	def getRuntime(self):
		return self.affirmModule('moai')

	def tryResizeCanvas(self, w,h ):
		ww, hh = self.window.width(), self.window.height()
		cw, ch = self.canvas.width(), self.canvas.height()
		self.window.resize( ww + w - cw, hh + h - ch)
		return True

	def copyFramebuffer( self ):
		image = self.canvas.grabFramebuffer()
		if image:
			clipboard = QtWidgets.QApplication.clipboard()
			clipboard.setImage( image )
			print('copied')

	def setOrientationPortrait( self ):
		if self.window.isFloating():
			pass #TODO
		getAKU().setOrientationPortrait()

	def setOrientationLandscape( self ):
		if self.window.isFloating():
			pass #TODO
		getAKU().setOrientationLandscape()

	def registerPreviewCanvas( self, clas, priority = 0 ):
		if not self.previewCanvasClas or self.previewCanvasClasPriority < priority:
			self.previewCanvasClasPriority = priority
			self.previewCanvasClas = clas

	def onLoad(self):
		self.window = self.requestDockWindow(
			'GamePreview',
			title = 'Game Preview',
			dock  = False,
			toolWindow = False
			)

		self.running = False
		self.paused = False
		
	
		self.updateTimer = None
		self.window.setFocusPolicy(Qt.StrongFocus)
		
		signals.connect( 'app.activate',   self.onAppActivate )
		signals.connect( 'app.deactivate', self.onAppDeactivate )
		
		signals.connect( 'debug.enter',    self.onDebugEnter )
		signals.connect( 'debug.exit',     self.onDebugExit )
		signals.connect( 'debug.stop',     self.onDebugStop )
		
		# signals.connect( 'game.pause',     self.onGamePause )
		# signals.connect( 'game.resume',    self.onGameResume )
		signals.connect( 'moai.reset',     self.onMoaiReset )

		signals.connect( 'module.loaded',     self.onModuleLoaded )
		
		self.menu = self.addMenu( 'main/preview', dict( label = 'Game' ) )

		self.menu.addChild([
				{'name':'start_game',  'label':'Resume Preview', 'shortcut':'meta+]' },
				{'name':'pause_game',  'label':'Pause Preview',  'shortcut':'meta+shit+]' },
				{'name':'stop_game',   'label':'Stop Preview',   'shortcut':'meta+[' },
				'----',
				{'name':'start_external_scene',  'label':'Run Scene',  'shortcut':'meta+alt+]' },
				{'name':'start_external_game',   'label':'Run Game',  'shortcut':'meta+alt+shift+]' },
				'----',
				{'name':'stay_on_top', 'label':'Stay On Top', 'type':'check', 'checked':self.getWorkspaceConfig('stay_on_top')},
				{'name':'pause_on_leave', 'label':'Pause On Leave', 'type':'check', 'checked':self.getWorkspaceConfig('pause_on_leave')},
				# '----',
				# {'name':'reset_moai',     'label':'RESET MOAI', 'shortcut':'Ctrl+Shift+R'}
			], self)

		# label = QtWidgets.QLabel()
		# label.setMinimumSize( 300, 20 )
		# label.setMaximumSize( 300, 20 )
		# self.toolbar.addWidget( label )
		# self.labelScreen = label
		self.onMoaiReset()

		##----------------------------------------------------------------##
		self.previewToolBar = self.addToolBar( 'game_preview_tools', 
			self.getMainWindow().requestToolBar( 'game_preview_tools' )
			)

		# self.addTool(	'game_preview_tools/play',
		# 	widget = SceneToolButton( 'scene_view_selection',
		# 		icon = 'tools/selection',
		# 		label = 'Selection'
		# 		)
		# 	)

		# self.addTool(	'game_preview_tools/stop',
		# 	widget = SceneToolButton( 'scene_view_translation',
		# 		icon = 'tools/translation',
		# 		label = 'Translation'
		# 		)
		# 	)

		self.addTool(	'game_preview_tools/run_external',
			label = 'Play External',
			icon = 'tools/run_external',
			)

		self.addTool(	'game_preview_tools/run_game_external',
			label = 'Play Game External',
			icon = 'tools/run_game_external',
			)
		

		self.enableMenu( 'main/preview/pause_game',  False )
		self.enableMenu( 'main/preview/stop_game',   False )

	def onStart( self ):
		self.canvas.startRefreshTimer( self.nonActiveFPS )
		pass
		

	def setupCanvas( self ):
		if self.previewCanvasClas:
			canvas = self.previewCanvasClas( self.window, context_prefix = 'game_preview' )
		else:
			canvas = GamePreviewCanvas( self.window, context_prefix = 'game_preview' )

		self.canvas = canvas
		self.canvas.module = self
		self.window.addWidget( self.canvas )


	def setupToolbar( self ):
		tool = self.window.addWidget( QtWidgets.QToolBar( self.window ), expanding = False )
		self.qtool = tool
		self.toolbar = self.addToolBar( 'game_preview', tool )

		# self.addTool( 'game_preview/----' )
		# self.addTool( 'game_preview/toggle_stay_top', label = 'Stay Top', type = 'check' )
		# self.addTool( 'game_preview/switch_screen_profile', label = 'Screen Profile' )
		self.addTool( 'game_preview/size_original', label = 'Reset Size', icon = 'reset' )
		self.addTool( 'game_preview/----' )
		self.addTool( 'game_preview/copy_framebuffer', label = 'Copy Framebuffer', icon = 'clipboard' )
		

	def onModuleLoaded( self ):
		self.setupCanvas()
		self.setupToolbar()
		
	def onAppReady( self ):
		pass

	def confirmStop( self ):
		if self.running:
			alertMessage( 'Preview is running', 'Stop game preview before close Gii' )
			return False
		else:
			return True

	def onStop( self ):
		if self.updateTimer:
			self.updateTimer.stop()

	def show( self ):
		self.window.setWindowFlags( Qt.Window )
		self.window.show()

	def hide( self ):
		self.window.hide()

	def refresh( self ):
		if self.canvas.isVisible():
			# self.canvas.makeCurrentCanvas()
			self.canvas.update()

	def updateView(self):
		if not self.running: return
		if self.paused: return
		runtime = self.getRuntime()

		self.canvas.makeCurrent()
		runtime.updateAKU()
		self.canvas.updateGL()

	def resizeView(self, w,h):
		self.viewWidth  = w
		self.viewHeight = h
		runtime = self.getRuntime()
		getAKU().setViewSize(w,h)
		# getAKU().setScreenSize(w,h)

	def renderView(self):
		runtime = self.getRuntime()
		runtime.renderAKU()

	def setTargetScreenSize( self, w, h ):
		self.targetScreenSize = ( w, h )

	def getTargetScreenSize( self ):
		return self.targetScreenSize

	def onMoaiReset( self ):
		runtime = self.getRuntime()
		runtime.addDefaultInputDevice( 'device' )
	
	def onDebugEnter(self):
		self.paused = True
		self.getRuntime().pause()
		self.window.setFocusPolicy(Qt.NoFocus)

	def onDebugExit(self, cmd=None):
		self.paused = False
		self.getRuntime().resume()
		self.window.setFocusPolicy(Qt.StrongFocus)
		if self.pendingScript:
			script = self.pendingScript
			self.pendingScript=False
			self.restartScript(script)
		self.setFocus()
		
	def onDebugStop(self):
		self.paused = True

	def onSetFocus(self):
		self.window.show()
		self.window.raise_()
		self.window.setFocus()
		self.canvas.setFocus()
		self.canvas.activateWindow()
		self.setActiveWindow( self.window )

	def startPreview( self ):
		if ( self.running and not self.paused ): return

		runtime = self.getRuntime()
		
		self.canvas.setInputDevice( runtime.getInputDevice('device') )
		self.canvas.startRefreshTimer( self.activeFPS )
		self.canvas.interceptShortcut = True
		self.getApp().setMinimalMainLoopBudget()
		jhook = self.getModule( 'joystick_hook' )
		if jhook:
			jhook.refreshJoysticks()
			jhook.setInputDevice( runtime.getInputDevice('device') )

		self.enableMenu( 'main/preview/pause_game', True )
		self.enableMenu( 'main/preview/stop_game',  True )
		self.enableMenu( 'main/preview/start_game', False )

		if not self.running: #start
			logging.info('start game preview')
			signals.emitNow( 'preview.start' )
			signals.emitNow( 'preview.resume' )
			self.running = True
			self.paused  = False
			self.updateTimer = self.window.startTimer( 60, self.updateView )
		else:
			if self.paused: #resume
				logging.info('resume game preview')
				signals.emitNow( 'preview.resume' )
				self.paused = False

		self.window.setWindowTitle( 'Game Preview [ RUNNING ]')
		self.qtool.setStyleSheet('QToolBar{ border-top: 1px solid rgb(0, 120, 0); }')
		runtime.resume()
		self.setFocus()
		logging.info('game preview started')

	def stopPreview( self ):
		if not self.running: return
		# self.canvas.makeCurrentCanvas()
		
		logging.info('stop game preview')
		self.canvas.setInputDevice( None )
		self.canvas.interceptShortcut = False
		jhook = self.getModule( 'joystick_hook' )
		if jhook: jhook.setInputDevice( None )
		
		self.getApp().resetMainLoopBudget()

		signals.emitNow( 'preview.stop' )
		self.updateTimer.stop()
		self.enableMenu( 'main/preview/stop_game',  False )
		self.enableMenu( 'main/preview/pause_game', False )
		self.enableMenu( 'main/preview/start_game', True )
		
		self.window.setWindowTitle( 'Game Preview' )
		self.qtool.setStyleSheet('QToolBar{ border-top: none; }')

		self.running = False
		self.paused  = False

		self.updateTimer = None
		self.canvas.startRefreshTimer( self.nonActiveFPS )
		logging.info('game preview stopped')

	
	def runGameExternal( self ):
		if self.running:
			alertMessage( 'running', 'Stop preview before running externally' )
			return False

		scnEditor = self.getModule( 'scenegraph_editor' )
		if scnEditor and scnEditor.activeSceneNode:
			scnEditor.saveScene()
		ExternRun.runGame( parent_window = self.getMainWindow() )


	def runSceneExternal( self ):
		if self.running:
			alertMessage( 'running', 'Stop preview before running externally' )
			return False
			
		scnEditor = self.getModule( 'scenegraph_editor' )
		if scnEditor and scnEditor.activeSceneNode:
			scnEditor.saveScene()
			path = scnEditor.activeSceneNode.getNodePath()
			ExternRun.runScene( path, parent_window = self.getMainWindow() )

	def pausePreview( self ):
		if ( not self.running ) or self.paused: return

		self.canvas.setInputDevice( None )
		jhook = self.getModule( 'joystick_hook' )
		if jhook: jhook.setInputDevice( None )

		self.getApp().resetMainLoopBudget()

		signals.emitNow( 'preview.pause' )
		logging.info('pause game preview')
		self.enableMenu( 'main/preview/start_game', True )
		self.enableMenu( 'main/preview/pause_game',  False )
		
		self.window.setWindowTitle( 'Game Preview[ Paused ]')
		self.qtool.setStyleSheet('QToolBar{ border-top: 1px solid rgb(255, 0, 0); }')

		self.paused = True
		self.getRuntime().pause()
		self.canvas.startRefreshTimer( self.nonActiveFPS )

	def onAppActivate(self):
		if self.waitActivate:
			self.waitActivate=False
			self.getRuntime().resume()

	def onAppDeactivate(self):
		if self.getWorkspaceConfig('pause_on_leave',False):
			self.waitActivate=True
			self.getRuntime().pause()

	def onMenu(self, node):
		name = node.name
		if name=='pause_on_leave':
			self.setWorkspaceConfig( 'pause_on_leave', node.getValue())

		elif name=='stay_on_top':
			self.setWorkspaceConfig( 'stay_on_top', node.getValue())
			self.window.setStayOnTop( node.getValue() )

		elif name=='reset_moai':
			#TODO: dont simply reset in debug
			# self.restartScript( self.runningScript )
			self.getRuntime().reset()

		elif name=='orient_portrait':
			self.setOrientationPortrait()

		elif name=='orient_landscape':
			self.setOrientationLandscape()

		elif name == 'start_game':
			self.startPreview()

		elif name == 'stop_game':
			self.stopPreview()

		elif name == 'pause_game':
			self.pausePreview()

		elif name == 'start_external_scene':
			self.runSceneExternal()
			
		elif name == 'start_external_game':
			self.runGameExternal()

	def onTool( self, tool ):
		name = tool.name
		if name == 'size_original':
			if self.targetScreenSize:
				w, h = self.targetScreenSize
				self.tryResizeCanvas(w,h)
			
		elif name == 'run_external':
			self.runSceneExternal()

		elif name == 'run_game_external':
			self.runGameExternal()

		elif name == 'copy_framebuffer':
			self.copyFramebuffer()

##----------------------------------------------------------------##
class GamePreviewCanvas(MOAICanvasBase):
	def __init__( self, *args, **kwargs ):
		super( GamePreviewCanvas, self ).__init__( *args, **kwargs )
		self.interceptShortcut = False
		self.installEventFilter( self )
		self.setObjectName( 'GamePreviewCanvas' )

	def eventFilter( self, obj, ev ):
		if not self.interceptShortcut: return False
		if obj == self:
			etype = ev.type()
			# if etype == QtCore.QEvent.KeyPress :
			# 	self.keyPressEvent( ev )
			# 	return True
			# elif etype == QtCore.QEvent.KeyRelease :
			# 	self.keyReleaseEvent( ev )
			# 	return True
			if etype == QtCore.QEvent.ShortcutOverride:
				self.keyPressEvent( ev )
				ev.accept()
				return True
		return False
		# return super( GamePreviewCanvas, self ).eventFilter( obj, ev )

	def resizeGL(self, width, height):
		ratio = self.devicePixelRatio()
		self.module.resizeView( width*ratio, height*ratio )
		self.updateGL()

	def onDraw(self):
		self.module.renderView()
		
##----------------------------------------------------------------##
GamePreview().register()
##----------------------------------------------------------------##

class RemoteCommandPreviewStart( RemoteCommand ):
	name = 'preview_start'
	def run( self, *args ):
		preview = app.getModule('game_preview')
		preview.startPreview()
		
class RemoteCommandPreviewStart( RemoteCommand ):
	name = 'preview_stop'
	def run( self, *args ):
		preview = app.getModule('game_preview')
		preview.stopPreview()

class RemoteCommandRunGame( RemoteCommand ):
	name = 'run_game'
	def run( self, *args ):
		preview = app.getModule('game_preview')
		preview.runGameExternal()
		
class RemoteCommandRunScene( RemoteCommand ):
	name = 'run_scene'
	def run( self, *args ):
		preview = app.getModule('game_preview')
		preview.runSceneExternal()

class RemoteCommandStopRunExtern( RemoteCommand ):
	name = 'stop_extern_run'
	def run( self, * args ):
		ExternRun.stopExternRun()

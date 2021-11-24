import subprocess
import os.path
import shutil
import time
import json

from gii.core         import *

from gii.SceneEditor  import SceneEditorModule

from mock import MOCKEditCanvas
from gii.moai.MOAIRuntime import getAKU
from gii.qt.dialogs                    import alertMessage, requestConfirm, requestString

from qtpy import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from mock import getMockClassName, _MOCK, _MOCK_EDIT
##----------------------------------------------------------------##

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

def _fixDuplicatedName( names, name, id = None ):
	if id:
		testName = name + '_%d' % id
	else:
		id = 0
		testName = name
	#find duplicated name
	if testName in names:
		return _fixDuplicatedName( names, name, id + 1)
	else:
		return testName

##----------------------------------------------------------------##
class GiiSyncSupport( SceneEditorModule ):
	name = 'gii_sync_support'
	dependencies = [ 'mock' ]

	def onLoad(self):
		self.addMenu( 'main/gii_sync', dict( label = 'Game Sync' ) )

		self.addMenuItem(
			'main/gii_sync/open_scene_from_game',
			dict( label='Open Gaming Scene' )
		)
		
		self.addMenuItem( 
			'main/gii_sync/----'
		)

		self.addMenuItem(
			'main/gii_sync/open_scene_in_game',
			dict( label='Open Editing Scene' )
		)

		self.addMenuItem( 
			'main/gii_sync/----'
		)

		self.addMenuItem(
			'main/gii_sync/start_remote_input',
			dict( label='Start Remote Input' )
		)
		
		##----------------------------------------------------------------##
		self.syncToolBar = self.addToolBar( 'gii_sync_tools', 
			self.getMainWindow().requestToolBar( 'gii_sync_tools' )
		)

		self.addTool(	'gii_sync_tools/sync_entity',
			label = 'Sync Entity',
			type = 'check'
		)

		self.addTool(	'gii_sync_tools/open_scene_in_game',
			label = 'Send Scene'
		)

		self.addTool(	'gii_sync_tools/open_scene_from_game',
			label = 'Get Scene'
		)

		self.addTool(	'gii_sync_tools/start_remote_input',
			label = 'Remote Input',
			shortcut = 'ctrl+alt+`'
		)

		signals.tryConnect ( 'console.exec_remote', self.execConsole )
		##----------------------------------------------------------------##
		self.optionSyncEntity = False

	def onAppReady(self):
		self.delegate = app.getModule('moai').loadLuaDelegate( 
			_getModulePath( 'GiiSyncSupport.lua' )
		)
		self.remoteInputDelegate = app.getModule('moai').loadLuaDelegate( 
			_getModulePath( 'GiiSyncRemoteInput.lua' )
		)

		signals.connect( 'entity.modified', self.onEntityModified  )
		signals.connect( 'entity.added',      self.onEntityAdded      )
		signals.connect( 'entity.removed',    self.onEntityRemoved    )
		signals.connect( 'component.added',      self.onComponentAdded      )
		signals.connect( 'component.removed',    self.onComponentRemoved    )

		signals.connect( 'scene.change',    self.onSceneChange   )
		signals.connect( 'scene.open',      self.onSceneOpen )

		self.syncTimer = self.addTimer( interval = 100 )
		self.syncTimer.setCallback( self.onSyncTimer )

		self.remoteInputWindow = RemoteInputWindow( self.remoteInputDelegate )
		self.remoteInputWindow.setFixedSize( 300, 200 )


	def isGameConnected( self ):
		return self.delegate.call( 'isGameConnected' )

	def execConsole(self,command):
		self.delegate.call( 'runScriptInGame', command )

	def query( self, key, callback = None, context = None, timeout = 2 ):
		return self.delegate.call( 'queryGame', key, context, callback )

	def queryAndWait( self, key, context = None, timeout = 2 ):
		self.queryReady = False
		self.queryResult = None
		def callback( peer, result ):
			self.queryReady = True
			self.queryResult = result
		self.delegate.call( 'queryGame', key, context, callback )
		t0 = time.perf_counter()
		while not self.queryReady:
			getAKU().updateSupport()
			elapsed = time.perf_counter() - t0
			if elapsed > timeout: break
			time.sleep( 0.005 )
		if not self.queryReady:
			return None
		else:
			return self.queryResult

	def startRemoteInput( self ):
		self.remoteInputWindow.setWindowModality( Qt.ApplicationModal )
		self.remoteInputWindow.show()
		self.remoteInputWindow.raise_()
		self.remoteInputWindow.centerCursor()

	def openGameSceneInEditor( self ):
		self.delegate.call( 'openSceneFromGame' )

	def openEditorSceneInGame( self ):
		self.delegate.call( 'openSceneInGame' )

	def onEntityModified( self, entity, *args ):
		if not self.optionSyncEntity: return
		self.delegate.call( 'notifyEntityModified', entity )

	def onEntityRemoved( self, entity, *args ):
		if not self.optionSyncEntity: return
		self.delegate.call( 'notifyEntityRemoved', entity )

	def onEntityAdded( self, entity, *args ):
		if not self.optionSyncEntity: return
		self.delegate.call( 'notifyEntityAdded', entity )

	def onComponentAdded( self, com, entity, *args ):
		if not self.optionSyncEntity: return
		self.delegate.call( 'notifyComponentAdded', com, entity )

	def onComponentRemoved( self, com, entity, *args ):
		if not self.optionSyncEntity: return
		self.delegate.call( 'notifyComponentRemoved', com, entity )

	def onSceneChange( self ):
		self.delegate.call( 'notifySceneChange' )

	def onSceneOpen( self, sceneNode, scene ):
		pass
		# if self.isGameConnected():
		# 	if requestConfirm( 'open scene in game?', 'Open scene in connected game?' ):
		# 		self.openEditorSceneInGame()

	def onSyncTimer( self ):
		if self.optionSyncEntity:
			self.delegate.call( 'flushEntitySync' )

	def onMenu( self, item ):
		name = item.name
		if name == 'open_scene_from_game':
			self.openGameSceneInEditor()

		elif name == 'open_scene_in_game':
			self.openEditorSceneInGame()

		elif name == 'start_remote_input':
			self.startRemoteInput()

	def updateOptions( self ):
		self.optionSyncEntity  = bool(self.getToolValue( 'gii_sync_tools/sync_entity' ) )
		self.delegate.call( 'updateOptions', {
				'syncEntity' : self.optionSyncEntity,
			}
		)
		if self.optionSyncEntity:
			self.syncTimer.start()
		else:
			self.syncTimer.stop()

	def onTool( self, tool ):
		name = tool.name
		if name == 'sync_entity':
			self.updateOptions()

		elif name == 'open_scene_in_game':
			if not self.isGameConnected():
				alertMessage( 'No Game', 'No Game connected', 'info' )
				return
			self.openEditorSceneInGame()

		elif name == 'open_scene_from_game':
			if not self.isGameConnected():
				alertMessage( 'No Game', 'No Game connected', 'info' )
				return
			self.openGameSceneInEditor()

		elif name == 'start_remote_input':
			self.startRemoteInput()


##----------------------------------------------------------------##


QTKeymap={
	205 : "lalt" ,
	178 : "pause" ,
	255 : "menu" ,
	44  : "," ,
	39  : "'" ,
	48  : "0" ,
	52  : "4" ,
	56  : "8" ,
	180 : "sysreq" ,
	64  : "@" ,
	174 : "return" ,
	55  : "7" ,
	92  : "\\" ,
	176 : "insert" ,
	68  : "d" ,
	72  : "h" ,
	76  : "l" ,
	80  : "p" ,
	84  : "t" ,
	88  : "x" ,
	190 : "right" ,
	204 : "lmeta" ,
	170 : "escape" ,
	186 : "home" ,
	96  : "`" ,
	32  : "space" ,
	51  : "3" ,
	173 : "backspace" ,
	193 : "pagedown" ,
	47  : "/" ,
	59  : ";" ,
	208 : "scrolllock" ,
	91  : "[" ,
	67  : "c" ,
	90  : "z" ,
	71  : "g" ,
	202 : "lshift" ,
	75  : "k" ,
	79  : "o" ,
	83  : "s" ,
	87  : "w" ,
	177 : "delete" ,
	191 : "down" ,
	46  : "." ,
	50  : "2" ,
	54  : "6" ,
	58  : ":" ,
	66  : "b" ,
	70  : "f" ,
	74  : "j" ,
	192 : "pageup" ,
	189 : "up" ,
	78  : "n" ,
	82  : "r" ,
	86  : "v" ,
	229 : "f12" ,
	230 : "f13" ,
	227 : "f10" ,
	228 : "f11" ,
	231 : "f14" ,
	232 : "f15" ,
	203 : "lctrl" ,
	218 : "f1" ,
	219 : "f2" ,
	220 : "f3" ,
	221 : "f4" ,
	222 : "f5" ,
	223 : "f6" ,
	224 : "f7" ,
	225 : "f8" ,
	226 : "f9" ,
	171 : "tab" ,
	207 : "numlock" ,
	187 : "end" ,
	45  : "-" ,
	49  : "1" ,
	53  : "5" ,
	57  : "9" ,
	61  : "=" ,
	93  : "]" ,
	65  : "a" ,
	69  : "e" ,
	73  : "i" ,
	77  : "m" ,
	81  : "q" ,
	85  : "u" ,
	89  : "y" ,
	188 : "left" ,
}


def convertKeyCode(k):
	if k > 1000: k = ( k & 0xff ) + ( 255 - 0x55 )
	return QTKeymap.get(k, k)

##----------------------------------------------------------------##
class RemoteInputWindow( QtWidgets.QWidget ):
	"""docstring for RemoteInputWindow"""
	def __init__( self, delegate, *args, **kwargs ):
		super( RemoteInputWindow, self ).__init__( *args, **kwargs )
		self.delegate = delegate
		self.retainedModifierState = None
		self.modifierShift = 0
		self.modifierCtrl = 0
		self.modifierAlt = 0
		self.modifierMeta = 0
		self.pixelRatio = 1
		self.cx = 0
		self.cy = 0
		self.setMouseTracking( True )
		self.setWindowTitle( 'press CMD+Option+` to close' )

	def mousePressEvent(self, event):
		button=event.button()		
		ratio = self.pixelRatio
		x,y=event.x() * ratio, event.y() * ratio
		btn=None
		if button==Qt.LeftButton:
			btn='left'
		elif button==Qt.RightButton:
			btn='right'
		elif button==Qt.MiddleButton:
			btn='middle'
		self.delegate.luaEnv.onMouseDown(btn)

	def mouseReleaseEvent(self, event):
		button=event.button()		
		ratio = self.pixelRatio
		x,y=event.x() * ratio, event.y() * ratio
		btn=None
		if button==Qt.LeftButton:
			btn='left'
		elif button==Qt.RightButton:
			btn='right'
		elif button==Qt.MiddleButton:
			btn='middle'
		self.delegate.luaEnv.onMouseUp(btn)

	def centerCursor( self ):
		self.cx = self.width()/2
		self.cy = self.height()/2
		p = self.mapToGlobal( QtCore.QPoint( self.cx, self.cy ) )
		QtGui.QCursor.setPos( p )

	def mouseMoveEvent(self, event):
		ratio = self.pixelRatio
		x,y = event.x() * ratio, event.y() * ratio
		dx = x - self.cx
		dy = y - self.cy
		if dx != 0 and dy != 0:
			self.delegate.luaEnv.onMouseMove( dx, dy )
		self.centerCursor()

	def wheelEvent(self, event):
		dx = 0
		dy = 0
		delta = event.angleDelta()
		dx = delta.x()
		dy = delta.y()
		x,y = event.x(), event.y()
		self.delegate.luaEnv.onMouseScroll( dx, dy, x, y )

	def refreshModifiers( self ):
		state = QtWidgets.QApplication.queryKeyboardModifiers()
		modifierShift = state & Qt.ShiftModifier
		modifierCtrl  = state & Qt.ControlModifier
		modifierAlt   = state & Qt.AltModifier
		modifierMeta  = state & Qt.MetaModifier
		if int(self.modifierShift) != int( modifierShift ):
			if modifierShift:
				self.delegate.luaEnv.onKeyDown( 'lshift' )
			else:
				self.delegate.luaEnv.onKeyUp( 'lshift' )

		if int(self.modifierCtrl) != int( modifierCtrl ):
			if modifierCtrl:
				self.delegate.luaEnv.onKeyDown( 'lctrl'  )
			else:
				self.delegate.luaEnv.onKeyUp( 'lctrl'  )

		if int(self.modifierAlt) != int( modifierAlt ):
			if modifierAlt:
				self.delegate.luaEnv.onKeyDown( 'lalt'   )
			else:
				self.delegate.luaEnv.onKeyUp( 'lalt'   )

		if int(self.modifierMeta) != int( modifierMeta ):
			if modifierMeta:
				self.delegate.luaEnv.onKeyDown( 'lmeta'   )
			else:
				self.delegate.luaEnv.onKeyUp( 'lmeta'   )
		self.modifierShift = modifierShift
		self.modifierCtrl = modifierCtrl
		self.modifierAlt = modifierAlt
		self.modifierMeta = modifierMeta

	def keyPressEvent(self, event):
		if event.isAutoRepeat(): return
		key = event.key()
		if key == Qt.Key_Shift:
			if not self.modifierShift:
				self.modifierShift = True
				self.delegate.luaEnv.onKeyDown( 'lshift' )

		elif key == Qt.Key_Control:
			if not self.modifierCtrl:
				self.modifierCtrl = True
				self.delegate.luaEnv.onKeyDown( 'lctrl' )

		elif key == Qt.Key_Meta:
			if not self.modifierMeta:
				self.modifierMeta = True
				self.delegate.luaEnv.onKeyDown( 'lmeta' )

		elif key == Qt.Key_Alt:
			if not self.modifierAlt:
				self.modifierAlt = True
				self.delegate.luaEnv.onKeyDown( 'lalt' )

		else:
			if key == 96 and self.modifierAlt and self.modifierCtrl:
				self.hide()
				self.setWindowModality( Qt.NonModal )
				return
			self.delegate.luaEnv.onKeyDown(convertKeyCode(key))
			if event.text():
				self.delegate.luaEnv.onKeyChar( event.text() )

		
	def keyReleaseEvent(self, event):
		key=event.key()

		if key == Qt.Key_Shift:
			state = QtWidgets.QApplication.queryKeyboardModifiers()
			self.modifierShift = state & Qt.ShiftModifier
			if not self.modifierShift:
				self.delegate.luaEnv.onKeyUp( 'lshift' )

		elif key == Qt.Key_Control:
			state = QtWidgets.QApplication.queryKeyboardModifiers()
			self.modifierCtrl = state & Qt.ControlModifier
			if not self.modifierCtrl:
				self.delegate.luaEnv.onKeyUp( 'lctrl' )

		elif key == Qt.Key_Meta:
			state = QtWidgets.QApplication.queryKeyboardModifiers()
			self.modifierMeta = state & Qt.MetaModifier
			if not self.modifierMeta:
				self.delegate.luaEnv.onKeyUp( 'lmeta' )

		elif key == Qt.Key_Alt:
			state = QtWidgets.QApplication.queryKeyboardModifiers()
			self.modifierAlt = state & Qt.AltModifier
			if not self.modifierAlt:
				self.delegate.luaEnv.onKeyUp( 'lalt' )

		else:
			self.delegate.luaEnv.onKeyUp(convertKeyCode(key))


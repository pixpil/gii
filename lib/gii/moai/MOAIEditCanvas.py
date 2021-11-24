import os.path
import time
from time import time as getTime

from qtpy import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt
from qtpy.QtCore import QEvent, QObject

from gii import *

from gii.qt.controls.GLWidget import GLWidget
from .MOAIRuntime              import getAKU, MOAIRuntime, MOAILuaDelegate
from .MOAICanvasBase           import MOAICanvasBase
from gii.qt.CursorCache                  import getCursor


from . import ContextDetection

def isBoundMethod( v ):
	return hasattr(v,'__func__') and hasattr(v,'im_self')

def boundToClosure( value ):
	if isBoundMethod( value ):
		func = value
		value = lambda *args: func(*args)
	return value
		

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

class MOAIEditCanvasLuaDelegate(MOAILuaDelegate):
	#Add some shortcuts
	def clearLua(self):
		super(MOAIEditCanvasLuaDelegate, self).clearLua()
		self._onMouseDown  = None
		self._onMouseUp    = None
		self._onMouseMove  = None
		self._onMouseEnter = None
		self._onMouseLeave = None
		self._onMouseScroll= None
		self._onKeyDown    = None
		self._onKeyUp      = None

		self._onTabletDown = None
		self._onTabletUp   = None
		self._onTabletMove = None

		self._onResize     = None
		self._preDraw      = None
		self._postDraw     = None
		self._onUpdate     = None

	def load(self, scriptPath, scriptEnv = None ):
		super( MOAIEditCanvasLuaDelegate, self ).load( scriptPath, scriptEnv )
		env = self.luaEnv
		if not env:
			raise Exception( 'failed loading editcanvas script:%s' % scriptPath )
		self.updateHooks()

	def updateHooks( self ):
		env = self.luaEnv
		if not env: return
		self._onMouseDown  = env.onMouseDown
		self._onMouseUp    = env.onMouseUp
		self._onMouseMove  = env.onMouseMove
		self._onMouseLeave = env.onMouseLeave
		self._onMouseEnter = env.onMouseEnter

		self._onMouseScroll     = env.onMouseScroll
		self._onKeyDown    = env.onKeyDown
		self._onKeyUp      = env.onKeyUp

		self._onResize     = env.onResize
		self._preDraw      = env.preDraw
		self._postDraw     = env.postDraw
		self._onUpdate     = env.onUpdate

		self._onTabletDown = env.onTabletDown
		self._onTabletUp   = env.onTabletUp
		self._onTabletMove = env.onTabletMove

	def onMouseDown(self, btn, x,y):
		if self._onMouseDown:	self._onMouseDown(btn, x,y)

	def onMouseUp(self, btn, x,y):
		if self._onMouseUp: self._onMouseUp(btn, x,y)

	def onMouseMove(self, x,y):
		if self._onMouseMove: self._onMouseMove(x,y)

	def onMouseEnter(self):
		if self._onMouseEnter: self._onMouseEnter()

	def onMouseLeave(self):
		if self._onMouseLeave: self._onMouseLeave()

	def onMouseScroll(self, dx, dy, x, y):
		if self._onMouseScroll: self._onMouseScroll(dx,dy,x,y)

	def onKeyDown(self, key):
		if self._onKeyDown: self._onKeyDown(key)

	def onKeyUp(self, key):
		if self._onKeyUp: self._onKeyUp(key)

	def onTabletDown(self, x, y, pressure, xTilt, yTilt ):
		if self._onTabletDown: self._onTabletDown(x, y, pressure, xTilt, yTilt )

	def onTabletUp(self, x, y, pressure, xTilt, yTilt ):
		if self._onTabletUp: self._onTabletDown(x, y, pressure, xTilt, yTilt )

	def onTabletMove(self, x, y, pressure, xTilt, yTilt ):
		if self._onTabletMove: self._onTabletDown(x, y, pressure, xTilt, yTilt )
	
	def onUpdate(self, step):
		if self._onUpdate: self._onUpdate(step)

	def preDraw(self):
		if self._preDraw: self._preDraw()

	def postDraw(self):
		if self._postDraw: self._postDraw()

	def onResize(self,w,h):
		if self._onResize: self._onResize(w,h)

##----------------------------------------------------------------##
class MOAIEditCanvasBase( MOAICanvasBase ):
	_id = 0
	def __init__( self, *args, **kwargs ):
		MOAIEditCanvas._id += 1
		super(MOAIEditCanvasBase, self).__init__( *args )

		contextPrefix = kwargs.get( 'context_prefix', 'edit_canvas')
		self.clearColor  = kwargs.get( 'clear_color', ( 0, 0, 0, 1 ) )
		self.runtime     = app.affirmModule( 'moai' )
		self.setContextName( '%s<%d>' % ( contextPrefix, MOAIEditCanvas._id ) )
		self.setObjectName( self.contextName )
		self.delegate    = MOAIEditCanvasLuaDelegate( self, autoReload = False )
		self.updateTimer = QtCore.QTimer(self)
		self.updateTimer.setTimerType( Qt.PreciseTimer )
		
		self.viewWidth   = 0
		self.viewHeight  = 0
		self.scriptEnv   = None
		self.scriptPath  = None
		self.lastUpdateTime = 0 
		self.updateStep  = 0
		self.alwaysForcedUpdate = False

		self.currentCursorId = 'arrow'
		self.cursorHidden = False

		self.updateTimer.timeout.connect( self.updateCanvas )
		signals.connect('moai.reset', self.onMoaiReset)
		signals.connect('moai.clean', self.onMoaiClean)

	def enableTabletEvent( self ):
		self.setTabletTracking( True )

	def disableTabletEvent( self ):
		self.setTabletTracking( False )

	def hideCursor(self):
		self.cursorHidden = True
		self.updateCursor()

	def showCursor(self):
		self.cursorHidden = False
		self.updateCursor()

	def setCursorByName( self, id ):
		self.currentCursorId = id
		self.updateCursor()

	def setCursorPos(self,x,y):
		self.cursor().setPos(self.mapToGlobal(QtCore.QPoint(x,y)))

	def updateCursor( self ):
		if self.cursorHidden:
			self.setCursor(QtCore.Qt.BlankCursor)
			return
		else:
			cursor = getCursor( self.currentCursorId )
			if not cursor:
				cursor = QtCore.Qt.ArrowCursor
			self.setCursor( cursor )

	def getCanvasSize(self):
		return self.width(), self.height()

	def startUpdateTimer( self, fps ):
		step = 1000 / fps
		self.updateTimer.start( step )
		self.updateStep = 1.0/fps
		self.lastUpdateTime = getTime()

	def stopUpdateTimer(self):
		self.updateTimer.stop()

	def onMoaiReset( self ):
		self.setupContext()

	def onMoaiClean(self):
		self.stopUpdateTimer()
		self.stopRefreshTimer()

	def loadScript( self, scriptPath, env = None, **kwargs ):
		self.scriptPath = scriptPath
		self.scriptEnv  = env
		self.setupContext()

	def setDelegateEnv(self, key, value, autoReload=True):
		#convert bound method to closure
		self.delegate.setEnv(key, boundToClosure( value ), autoReload)

	def getDelegateEnv(self, key, defaultValue=None):
		return self.delegate.getEnv(key, defaultValue)
	
	def makeDelegateEnv( self ):
		return {
			'updateWidget'     : boundToClosure( self.update ),
			'updateCanvas'     : boundToClosure( self.updateCanvas_ ),
			'hideCursor'       : boundToClosure( self.hideCursor ),
			'showCursor'       : boundToClosure( self.showCursor ),
			'setCursor'        : boundToClosure( self.setCursorByName ),
			'setCursorPos'     : boundToClosure( self.setCursorPos ),
			'getCanvasSize'    : boundToClosure( self.getCanvasSize ),
			'startUpdateTimer' : boundToClosure( self.startUpdateTimer ),
			'stopUpdateTimer'  : boundToClosure( self.stopUpdateTimer ),
			'contextName'      : boundToClosure( self.contextName ),
			'getRenderContext' : boundToClosure( self.getRenderContext ),
			'enableTabletEvent' : boundToClosure( self.enableTabletEvent ),
			'disableTabletEvent' : boundToClosure( self.disableTabletEvent ),
		}

	def setupContext(self):
		self.setClearColor( self.clearColor )
		if self.scriptPath:
			self.makeCurrent()
			env = self.makeDelegateEnv()
			
			if self.scriptEnv:
				env.update( self.scriptEnv )
			self.delegate.load( self.scriptPath, env )

			self.delegate.safeCall( 'onLoad' )
			self.resizeGL(self.width(), self.height())
			self.startRefreshTimer()
			self.updateCanvas()

	def safeCall(self, method, *args):		 
		self.makeCurrentCanvas()
		return self.delegate.safeCall(method, *args)

	def call(self, method, *args):
		self.makeCurrentCanvas()
		return self.delegate.call(method, *args)

	def safeCallMethod(self, objId, method, *args):		 
		self.makeCurrentCanvas()
		return self.delegate.safeCallMethod(objId, method, *args)

	def callMethod(self, objId, method, *args):		 
		self.makeCurrentCanvas()
		return self.delegate.callMethod(objId, method, *args)

	def makeCurrentCanvas( self ):
		pass
		# self.runtime.changeRenderContext( self.contextName, self.viewWidth, self.viewHeight )

	def onDraw(self):
		runtime = self.runtime

		ctx = self.renderContext
		#lua
		ctx.makeCurrent( ctx )

		self.delegate.preDraw()
		#lua
		ctx.draw( ctx )
		self.delegate.postDraw()


	def updateCanvas_( self, forced = None, no_sim = True ):
		if forced == None: forced = self.alwaysForcedUpdate
		return self.updateCanvas( no_sim = no_sim != False, forced = forced )

	def updateCanvas( self, **option ):
		currentTime = getTime()
		duration = currentTime - self.lastUpdateTime
		self.lastUpdateTime = currentTime
		step = self.updateStep
		self.makeCurrentCanvas()
	
		noSim = option.get( 'no_sim', False )

		if noSim:
			# self.runtime.stepSim( 0 )
			self.runtime.updateNodeMgr()

		else:
			self.runtime.stepSim( step )
			
		self.runtime.stepGC( 100 )
		self.delegate.onUpdate( step )

		forced = option.get( 'forced', self.alwaysForcedUpdate )
		# printTraceBack()
		# print 'update canvas: %.3f' % ( duration )
		if forced:
			self.forceUpdateGL()
		else:
			self.updateGL()

	def resizeGL(self, width, height):
		super( MOAIEditCanvasBase, self ).resizeGL( width, height )
		self.delegate.onResize(width,height)
		self.viewWidth  = width
		self.viewHeight = height

	def refreshSize( self ):
		self.delegate.onResize( self.viewWidth, self.viewHeight )


##----------------------------------------------------------------##
class MOAIEditCanvas( MOAIEditCanvasBase ):
	def __init__( self, *args, **kwargs ):
		super( MOAIEditCanvas, self ).__init__( *args, **kwargs )
		self.modifierShift = 0
		self.modifierCtrl = 0
		self.modifierAlt = 0
		self.modifierMeta = 0

	def mousePressEvent(self, event):
		self.setFocus()
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
		self.makeCurrentCanvas()
		self.delegate.onMouseDown(btn, x,y)

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
		self.makeCurrentCanvas()
		self.delegate.onMouseUp(btn, x,y)

	def mouseMoveEvent(self, event):
		ratio = self.pixelRatio
		x,y=event.x() * ratio, event.y() * ratio
		self.makeCurrentCanvas()
		self.delegate.onMouseMove(x,y)

	def wheelEvent(self, event):
		dx = 0
		dy = 0
		delta = event.angleDelta()
		dx = delta.x()
		dy = delta.y()
		x,y=event.x(), event.y()
		self.makeCurrentCanvas()
		self.delegate.onMouseScroll( dx, dy, x, y )

	def enterEvent(self, event):
		# self.setFocus()
		self.makeCurrentCanvas()
		# self.restoreModifierState()
		self.refreshModifiers()
		self.delegate.onMouseEnter()

	def leaveEvent(self, event):
		self.makeCurrentCanvas()
		self.delegate.onMouseLeave()

	def focusInEvent( self, ev ):
		# self.restoreModifierState()
		self.refreshModifiers()
		return super( MOAIEditCanvas, self ).focusInEvent( ev )

	def focusOutEvent( self, ev ):
		# self.releaseModifierState()
		return super( MOAIEditCanvas, self ).focusOutEvent( ev )

	def refreshModifiers( self ):
		state = QtWidgets.QApplication.queryKeyboardModifiers()
		modifierShift = state & Qt.ShiftModifier
		modifierCtrl  = state & Qt.ControlModifier
		modifierAlt   = state & Qt.AltModifier
		modifierMeta  = state & Qt.MetaModifier

		if int(self.modifierShift) != int( modifierShift ):
			if modifierShift:
				self.delegate.onKeyDown( 'lshift' )
			else:
				self.delegate.onKeyUp( 'lshift' )

		if int(self.modifierCtrl) != int( modifierCtrl ):
			if modifierCtrl:
				self.delegate.onKeyDown( 'lctrl'  )
			else:
				self.delegate.onKeyUp( 'lctrl'  )

		if int(self.modifierAlt) != int( modifierAlt ):
			if modifierAlt:
				self.delegate.onKeyDown( 'lalt'   )
			else:
				self.delegate.onKeyUp( 'lalt'   )

		if int(self.modifierMeta) != int( modifierMeta ):
			if modifierMeta:
				self.delegate.onKeyDown( 'lmeta'   )
			else:
				self.delegate.onKeyUp( 'lmeta'   )

		self.modifierShift = modifierShift
		self.modifierCtrl = modifierCtrl
		self.modifierAlt = modifierAlt
		self.modifierMeta = modifierMeta

	def keyPressEvent(self, event):
		if event.isAutoRepeat(): return
		key = event.key()
		self.makeCurrentCanvas()
		if key == Qt.Key_Shift:
			if not self.modifierShift:
				self.modifierShift = True
				self.delegate.onKeyDown( 'lshift' )

		elif key == Qt.Key_Control:
			if not self.modifierCtrl:
				self.modifierCtrl = True
				self.delegate.onKeyDown( 'lctrl' )

		elif key == Qt.Key_Meta:
			if not self.modifierMeta:
				self.modifierMeta = True
				self.delegate.onKeyDown( 'lmeta' )

		elif key == Qt.Key_Alt:
			if not self.modifierAlt:
				self.modifierAlt = True
				self.delegate.onKeyDown( 'lalt' )

		else:
			self.delegate.onKeyDown(convertKeyCode(key))
		
	def keyReleaseEvent(self, event):
		key=event.key()
		self.makeCurrentCanvas()

		if key == Qt.Key_Shift:
			state = QtWidgets.QApplication.queryKeyboardModifiers()
			self.modifierShift = state & Qt.ShiftModifier
			if not self.modifierShift:
				self.delegate.onKeyUp( 'lshift' )

		elif key == Qt.Key_Control:
			state = QtWidgets.QApplication.queryKeyboardModifiers()
			self.modifierCtrl = state & Qt.ControlModifier
			if not self.modifierCtrl:
				self.delegate.onKeyUp( 'lctrl' )

		elif key == Qt.Key_Meta:
			state = QtWidgets.QApplication.queryKeyboardModifiers()
			self.modifierMeta = state & Qt.MetaModifier
			if not self.modifierMeta:
				self.delegate.onKeyUp( 'lmeta' )

		elif key == Qt.Key_Alt:
			state = QtWidgets.QApplication.queryKeyboardModifiers()
			self.modifierAlt = state & Qt.AltModifier
			if not self.modifierAlt:
				self.delegate.onKeyUp( 'lalt' )

		else:
			self.delegate.onKeyUp(convertKeyCode(key))

	def tabletEvent( self, event ):
		t = event.type()
		x = event.x()
		y = event.y()
		xTilt = event.xTilt()
		yTilt = event.yTilt()
		pressure = event.pressure()

		if t == QEvent.TabletPress:
			self.delegate.onTabletDown( x, y, pressure, xTilt, yTilt )

		elif t == QEvent.TabletRelease:
			self.delegate.onTabletUp( x, y, pressure, xTilt, yTilt )

		elif t == QEvent.TabletMove:
			self.delegate.onTabletMove( x, y, pressure, xTilt, yTilt )

		# event.accept()

from qtpy import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from gii.qt.controls.GLWidget import GLWidget
from . import ContextDetection

from .MOAIRuntime import getAKU, _GII


def convertKeyCode(k):
	if k>1000:
		return (k&0xff)+(255 - 0x55)
	else:
		return k


class MOAICanvasBase(GLWidget):
	def __init__( self, parentWidget = None, **option ):
		option['vsync'] = option.get('vsync', True)
		super(MOAICanvasBase,self).__init__( parentWidget, **option )		
		#empty
		self.contextName = 'MOAICanvasBase'
		self.renderContext = None
		self.inputDevice = None
		self.buttonCount = 0
		self.contextDetected = False
		#init context
		self.renderContext = ctx = self.createRenderContext()
		self.setFocusPolicy( Qt.WheelFocus )
		assert ctx

	def setContextName( self, name ):
		self.contextName = name
		ctx = self.renderContext
		ctx.setName( ctx, name )

	def createRenderContext( self ):
		assert not self.renderContext
		return _GII.GIIRenderContext()

	def onContextReady( self, ctx ):
		pass

	def resizeGL(self, width, height):
		ratio = self.devicePixelRatio()
		ctx = self.renderContext
		#lua call
		ctx.setSize( ctx, width, height, ratio )

	def makeCurrent( self ):
		ctx = self.renderContext
		if not self.contextDetected:
			ctx.detect( ctx )
			self.contextDetected = True
			self.onContextReady( ctx )
		ctx.makeCurrent( ctx )

	def setClearColor( self, color = None ): #tuple( r,g,b,a )
		ctx = self.renderContext
		if color:
			r,g,b,a = color
			ctx.setClearColor( ctx, r,g,b,a )
		else:
			ctx.setClearColor( ctx, False )

	def getRenderContext( self ):
		return self.renderContext

	def setInputDevice(self, device):
		self.inputDevice = device

	def mousePressEvent(self, event):	
		inputDevice = self.inputDevice
		if not inputDevice: return
		button = event.button()		
		if self.buttonCount == 0:
			self.grabMouse()
		self.buttonCount += 1
		inputDevice.getSensor('pointer').enqueueEvent(event.x(), event.y())
		if   button == Qt.LeftButton:
			inputDevice.getSensor('mouseLeft').enqueueEvent(True)
		elif button == Qt.RightButton:
			inputDevice.getSensor('mouseRight').enqueueEvent(True)
		elif button == Qt.MiddleButton:
			inputDevice.getSensor('mouseMiddle').enqueueEvent(True)

	def mouseReleaseEvent(self, event):
		inputDevice=self.inputDevice
		if not inputDevice: return
		self.buttonCount -= 1
		if self.buttonCount == 0:
			self.releaseMouse()
		button = event.button()
		inputDevice.getSensor('pointer').enqueueEvent(event.x(), event.y())
		if   button == Qt.LeftButton:
			inputDevice.getSensor('mouseLeft').enqueueEvent(False)
		elif button == Qt.RightButton:
			inputDevice.getSensor('mouseRight').enqueueEvent(False)
		elif button == Qt.MiddleButton:
			inputDevice.getSensor('mouseMiddle').enqueueEvent(False)

	def mouseMoveEvent(self, event):
		inputDevice=self.inputDevice
		if not inputDevice: return
		inputDevice.getSensor('pointer').enqueueEvent(event.x(), event.y())

	def wheelEvent(self, event):
		#TODO
		pass
		# steps = event.delta() / 120.0;
		# dx = 0
		# dy = 0
		# if event.orientation() == Qt.Horizontal : 
		# 	dx = steps
		# else:
		# 	dy = steps
		# x,y=event.x(), event.y()
		# self.delegate.onMouseScroll( dx, dy, x, y )

	def keyPressEvent(self, event):
		if event.isAutoRepeat(): return
		inputDevice=self.inputDevice
		if not inputDevice: return
		key=event.key()
		inputDevice.getSensor('keyboard').enqueueKeyEvent( convertKeyCode(key), True )

	def keyReleaseEvent(self, event):
		inputDevice=self.inputDevice
		if not inputDevice: return
		key=event.key()
		inputDevice.getSensor('keyboard').enqueueKeyEvent( convertKeyCode(key), False )


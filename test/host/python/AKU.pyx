STUFF = "Hi"
from AKU cimport *

import atexit

include '_lupa.pyx'

_aku=None

def _removeMoaiSingleton():
	global _aku
	if _aku:
		del _aku

def getAKU():
	global _aku
	if _aku:
		return _aku
	return AKU()

atexit.register(_removeMoaiSingleton)

cdef void _callbackOpenWindow( const_char_ptr title, int width, int height ):
	_aku.onOpenWindow(title, width, height)

cdef void _callbackEnterFullscreenMode():
	_aku.onEnterFullscreenMode()

cdef void _callbackExitFullscreenMode():
	_aku.onExitFullscreenMode()


cdef class AKU:
	cdef LuaRuntime lua
	cdef object _funcOpenWindow
	cdef object _funcEnterFS
	cdef object _funcExitFS
	cdef object _initialized

	def __cinit__(self):
		global _aku
		_aku = self
		
	def __dealloc__(self): 
		global _aku
		_aku = None
		self.deleteContext()
		if self._initialized:
			AKUAppFinalize()

	def __init__( self ):
		self._initialized = False

	def createContext(self):
		if not self._initialized:
			AKUAppInitialize ()
			AKUModulesAppInitialize()
			self._initialized = True

		AKUCreateContext()

		AKUModulesContextInitialize()

		registerHelpers()
		registerExtensionClasses()

		# AKUAudioSamplerInit()
		
		AKUSetFunc_OpenWindow(_callbackOpenWindow)
		AKUSetFunc_ExitFullscreenMode(_callbackExitFullscreenMode)
		AKUSetFunc_EnterFullscreenMode(_callbackEnterFullscreenMode)

		cdef lua_State *L = AKUGetLuaState()
		self.lua=LuaRuntime()
		self.lua.initWithState(L)

	def setFuncOpenWindow(self, f):
		self._funcOpenWindow=f

	def setFuncEnterFullscreenMode(self, f):
		self._funcEnterFS=f

	def setFuncExitFullscreenMode(self, f):
		self._funcExitFS=f

	def getLuaRuntime(self):
		return self.lua

	def checkContext(self):
		return AKUGetContext() != 0

	def resetContext(self):
		self.deleteContext()
		self.createContext()

	def deleteContext(self):
		context=AKUGetContext()
		if context != 0:
			self.lua.destroy()
			self.lua = None
			AKUDeleteContext(context)
			self.finalize()

	def clearMemPool(self):
		AKUClearMemPool()

	def setScreenSize(self, w, h):
		AKUSetScreenSize(w,h)

	def setViewSize(self, w, h):
		AKUSetViewSize(w,h)

	def setOrientationLandscape(self):
		AKUSetOrientation(1)

	def setOrientationPortrait(self):
		AKUSetOrientation(0)

	def setWorkingDirectory(self, path):
		AKUSetWorkingDirectory(path)

	def reserveInputDevices(self, count):
		AKUReserveInputDevices(count)

	def reserveInputDeviceSensors(self, devId, count):
		AKUReserveInputDeviceSensors(devId, count)

	def setInputConfigurationName(self, name):
		AKUSetInputConfigurationName(name)

	def setInputDevice(self, id, name):
		AKUSetInputDevice(id, name)

	def setInputDeviceKeyboard(self, devId, sensorId, name):
		AKUSetInputDeviceKeyboard(devId, sensorId, name)

	def setInputDevicePointer(self, devId, sensorId, name):
		AKUSetInputDevicePointer(devId, sensorId, name)

	def setInputDeviceWheel(self, devId, sensorId, name):
		AKUSetInputDeviceWheel(devId, sensorId, name)

	def setInputDeviceButton(self, devId, sensorId, name):
		AKUSetInputDeviceButton(devId, sensorId, name)

	def setInputDeviceTouch(self, devId, sensorId, name):
		AKUSetInputDeviceTouch(devId, sensorId, name)

	def setInputDeviceCompass(self, devId, sensorId, name):
		AKUSetInputDeviceCompass(devId, sensorId, name)

	def setInputDeviceLevel(self, devId, sensorId, name):
		AKUSetInputDeviceLevel(devId, sensorId, name)

	def setInputDeviceJoystickEx(self, devId, sensorId, name):
		AKUSetInputDeviceJoystickEx(devId, sensorId, name)

	def enqueueButtonEvent(self, deviceID, sensorID, down):
		AKUEnqueueButtonEvent(deviceID, sensorID, down)

	def enqueueWheelEvent(self, deviceID, sensorID, value):
		AKUEnqueueWheelEvent(deviceID, sensorID, value)

	def enqueueTouchEvent(self, deviceID, sensorID, touchID, down, x, y):
		AKUEnqueueTouchEvent(deviceID, sensorID, touchID, down, x, y)

	def enqueueTouchEventCancel(self, deviceID, sensorID):
		AKUEnqueueTouchEventCancel(deviceID, sensorID)

	def enqueuePointerEvent(self, deviceID, sensorID, x, y):
		AKUEnqueuePointerEvent(deviceID, sensorID, x, y)

	def enqueueCompassEvent(self, deviceID, sensorID, heading):
		AKUEnqueueCompassEvent(deviceID, sensorID, heading)

	def enqueueKeyboardKeyEvent(self, deviceID, sensorID, keyID, down):
		AKUEnqueueKeyboardKeyEvent(deviceID, sensorID, keyID, down)

	def enqueueKeyboardCharEvent(self, deviceID, sensorID, character ):
		AKUEnqueueKeyboardCharEvent(deviceID, sensorID, character)

	def enqueueKeyboardTextEvent(self, deviceID, sensorID, text):
		AKUEnqueueKeyboardTextEvent(deviceID, sensorID, text)

	def enqueueLevelEvent(self, deviceID, sensorID, x, y, z):
		AKUEnqueueLevelEvent(deviceID, sensorID, x, y, z)

	def enqueueJoystickExButtonEvent(self, deviceID, sensorID, buttonID, down):
		AKUEnqueueJoystickExButtonEvent(deviceID, sensorID, buttonID, down)

	def enqueueJoystickExAxisEvent(self, deviceID, sensorID, axisID, value):
		AKUEnqueueJoystickExAxisEvent(deviceID, sensorID, axisID, value)

	def update(self):
		AKUModulesUpdate()
		
	def pause(self, paused=True):
		AKUPause(paused)

	def render(self):
		AKURender()

	def detectGfxContext(self):
		AKUDetectGfxContext()

	def finalize(self):
		AKUModulesAppFinalize()
		
	def runString(self, text):
		AKULoadFuncFromString( text )
		AKUCallFunc()

	def runScript(self, filename):
		AKULoadFuncFromFile( filename )
		AKUCallFunc()

	def evalString(self, text):
		return self.lua.eval(text)

	def onOpenWindow(self, title, width, height):
		if self._funcOpenWindow:
			self._funcOpenWindow(title, width, height)

	def onEnterFullScreen(self):
		if self._funcEnterFS:
			self._funcEnterFS()

	def onExitFullScreen(self):
		if self._funcExitFS:
			self._funcExitFS()
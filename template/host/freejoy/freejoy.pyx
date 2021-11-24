from freejoy cimport *

_JOY_X      = 0
_JOY_Y      = 1
_JOY_Z      = 2
_JOY_R      = 3
_JOY_U      = 4
_JOY_V      = 5
_JOY_YAW    = 6
_JOY_PITCH  = 7
_JOY_ROLL   = 8
_JOY_HAT    = 9
_JOY_WHEEL  = 10

def getJoystickCount():
	return JoyCount()

cdef class Joystick:
	cdef int port
	cdef int pollTime
	cdef int buttonStates
	cdef int[ 16 ] hitCounts
	cdef float[ 16 ] axisStates
	cdef object buttonListener
	cdef object axisListener
	cdef object context

	def __cinit__( self ):
		pass

	def __init__( self, port ):
		self.port = port
		self.flush()
		self.buttonListener = None
		self.axisListener   = None
		self.context        = None

	def getPort( self ):
		return self.port

	def setContext( self, context ):
		self.context = context

	def getContext( self ):
		return self.context

	def setButtonListener( self, listener ):
		self.buttonListener =  listener

	def setAxisListener( self, listener ):
		self.axisListener =  listener
	
	def poll( self ):
		cdef int buttonStates1
		cdef int buttonStates0
		cdef float[ 16 ] axisStates1
		for i in range( 0, 16 ):
			axisStates1[ i ] = 0
		ReadJoy( self.port, &buttonStates1, &axisStates1[ 0 ] )
		buttonStates0 = self.buttonStates

		axisListener   = self.axisListener
		buttonListener = self.buttonListener

		if buttonListener and buttonStates1 != buttonStates0:
			for i in range( 0, 16 ):
				mask = 1 << i
				b0 = buttonStates0 & mask != 0
				b1 = buttonStates1 & mask != 0
				if b0 != b1:
					buttonListener( self, i, b1 )
		self.buttonStates = buttonStates1
		
		if axisListener:
			for i in range( 0, 16 ):
				v0 = self.axisStates[ i ]
				v1 = axisStates1[ i ]
				diff = v0 - v1
				if diff < -0.01 or diff > 0.01:
					self.axisStates[ i ] = v1
					axisListener( self, i, v1 )
		else:
			for i in range( 0, 16 ):
				self.axisStates[ i ] = axisStates1[ i ]

	def flush( self ):
		for i in range( 0, 16 ):
			self.hitCounts[ i ] = 0
			self.axisStates[ i ] = 0

	def getName( self ):
		return <bytes> JoyCName( self.port )

	def getButtonCaps( self ):
		return JoyButtonCaps( self.port )

	def isValid( self ):
		return JoyCount() > self.port

	def getX( self ):
		return self.axisStates[ _JOY_X ]

	def getY( self ):
		return self.axisStates[ _JOY_Y ]

	def getZ( self ):
		return self.axisStates[ _JOY_Z ]

	def isDown( self, button ):
		return self.buttonStates & ( 1 << button ) != 0

	def getR( self ):
		return self.axisStates[ _JOY_R ]

	def getU( self ):
		return self.axisStates[ _JOY_U ]

	def getV( self ):
		return self.axisStates[ _JOY_V ]

	def getYaw( self ):
		return self.axisStates[ _JOY_YAW ]

	def getPitch( self ):
		return self.axisStates[ _JOY_PITCH ]

	def getRoll( self ):
		return self.axisStates[ _JOY_ROLL ]

	def getAxis( self, i ):
		return self.axisStates[ min( max( i, 0 ), 16 ) ]

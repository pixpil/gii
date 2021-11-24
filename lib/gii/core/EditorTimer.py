import weakref

class EditorTimer(object):
	def __init__( self, **kwargs ):
		frequency = kwargs.get( 'frequency', None )  
		if not frequency:
			interval = kwargs.get( 'interval', 1000 ) 
		else:
			if frequency <= 0:
				raise ValueError( 'invalid frequency' )
			interval = 1000 / frequency
		self.interval = interval
		self.started = False
		self.paused  = False
		self.destroyed = False
		self.destroyOnStop = kwargs.get( 'destroy_on_stop', False )
		self.singleshot = kwargs.get( 'singleshot', False )
		# self.tickFunc = None
		self.totalTime = 0
		self.frameTime = 0
		self.onTick = None

	def setCallback( self, callback ):
		self.onTick = callback

	def getInterval( self ):
		return self.interval

	def setInterval( self , interval ):
		self.interval = interval

	def setDestroyOnStop( self, destroy ):
		self.destroyOnStop = destroy

	def setSingleShot( self, single ):
		self.singleshot = single

	def isSingleShot( self, single ):
		return self.singleshot

	def getTime( self ):
		return self.totalTime

	def pause( self, paused = True ):
		self.paused = paused

	def resume( self ):
		self.pause( False )

	def start( self ):
		self.started = True
		self.totalTime = 0
		self.frameTime = 0

	def stop( self ):
		self.started = False
		if self.destroyOnStop:
			self.destroyed = True

	def update( self, dt ):
		if self.paused: return
		if not self.started: return
		ft1 = self.frameTime + dt
		self.totalTime = tt1 = self.totalTime + dt
		interval = self.interval
		while ft1 > interval:
			ft1 -= interval
			self.tick( tt1 )
			if not self.paused: return
			if not self.started: return
		self.frameTime = ft1

	def tick( self, tt1 ):
		if self.onTick:
			self.onTick()
		if self.singleshot:
			self.stop()

	def destroy( self ):
		self.stop()
		self.destroyed = True
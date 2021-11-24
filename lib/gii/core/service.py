##----------------------------------------------------------------##
class Service(object):
	def __init__( self ):
		self.state = 'stop'
		self.activeInstances = []

	def getId( self ):
		raise Exception( 'getId() not implemented' )

	def startInstance( self ):
		instance = ServiceInstance( self )
		self.onInstanceStart( instance )

	def stopInstance( self, instance ):
		self.onInstanceStop( instance )
		return True

	def stop( self ):
		instances = self.activeInstances
		self.activeInstances = []
		for instance in instances:
			if not self.stopInstance( instance ): #not shutdown successfuly
				self.activeInstances.append( instance )
			
		self.activeInstances = {}
		self.state = 'stop'

	def start( self ):
		self.state = 'running'

	#override these
	def onInstanceStart( self, instance ):
		pass

	def onInstanceStop( self, instance ):
		pass


##----------------------------------------------------------------##
class ServiceInstance(object):
	def __init__( self, service ):
		self.service = service
		self.state = 'stop'

	def stop( self ):
		self.service.stopInstance( self )


import os

#TODO:....
##----------------------------------------------------------------##
class HostTarget(object):
	def build ( self, **option ):
		pass

	def run ( self, **option ):
		pass

	def deploy ( self, **option ):
		pass

##----------------------------------------------------------------##
_HostTargetClassRegistry = {}
def registerHostTargetClass( id, clas ):
	_DeployConfigClassRegistry[ id ] = clas
	clas.classId = id

def getHostTargetClass( id ):
	return _DeployConfigClassRegistry.get( id, None )

def getHostTargetClassRegistry( id ):
	return _DeployConfigClassRegistry


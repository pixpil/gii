from abc import ABCMeta, abstractmethod

##----------------------------------------------------------------##
_resGuardDictCache = {}
_resGuardDict = {}
def registerResGuard( typeId, guard ):
	_resGuardDict[ typeId ] = guard

def findResGuard( typeId ):
	g = _resGuardDictCache.get( typeId, None )
	if g is None:
		for typeId0, g1 in _resGuardDict:
			if issubclass( typeId, typeId0 ):
				g = g1
				break
		g = g or False
		_resGuardDictCache[ typeId ] = g
	return g


##----------------------------------------------------------------##
class ResGuardMeta( ABCMeta ):
	def __init__( cls, name, bases, dict ):
		super( ResGuardMeta, cls ).__init__( name, bases, dict )
		targetType       = dict.get( 'target', None )
		if targetType:
			m = cls()
			m._targetType = targetType
			registerResGuard( targetType, m )

##----------------------------------------------------------------##
class ResGuard(object, metaclass=ResGuardMeta):
	def onRelease( self, res ):
		pass


##----------------------------------------------------------------##
class ResRef(object):
	def __init__(self, data):
		self.data = data
	
	def __dealloc__( self ):
		self.release( self.data )

	def release( self, data ):
		typeId = type( data )
		guard = findResGuard( typeId )
		if guard:
			guard.onRelease( data )


##----------------------------------------------------------------##
class ResHolder(object):
	def retain( self, resource ):
		if not hasattr( self, '__resources' ):
			self.__resources = []
		guard = ResRef( resource )
		self.__resources.append( guard )

	def release( self, resource ):
		for i, guard in iter( self.__resources ):
			if guard.data is resource:
				self.__resources = self.__resources.pop( i )
				return

	def releaseAll( self ):
		self.__resources = []

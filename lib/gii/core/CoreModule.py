from .EditorModule import EditorModule

#for future refactoring...
class CoreModule( EditorModule ):
	_singleton=None

	@staticmethod
	def get():
		return CoreModule._singleton

	def __init__( self ):
		pass

	def getName( self ):
		return 'gii'

	def getDependency( self ):
		return []

	def getBaseDependency( self ):
		return []

	def onStart( self ):
		pass

CoreModule().register()

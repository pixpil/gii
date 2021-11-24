from .RemoteCommand import *

from .asset import *

##----------------------------------------------------------------##
class RemoteCommandSearchAsset( RemoteCommand ):
	name = 'search_asset'
	def run( self, *args ):
		if len( args ) >= 1:
			citeria = ' '.join( args )
			lib = AssetLibrary.get()
			result = lib.searchAsset( citeria )
			for node in result:
				print((node.getPath()))


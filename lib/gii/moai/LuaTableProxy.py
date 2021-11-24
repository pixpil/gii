##----------------------------------------------------------------##
class LuaTableProxy( object ):
	def __init__( self, _table ):
		self._setTarget( _table )

	def _setTarget( self, _table ):
		self.__dict__[ '_table' ] = _table

	def __getattr__( self, id ):
		return self.get(id)

	def __getitem__( self, id ):
		return self.get(id)

	def get( self, id, default = None ):		
		v = self._table[ id ]
		if v == None: return default
		return v

	def __setattr__( self, id, v ):
		return self.set(id, v)

	def __setitem__( self, id, v ):
		return self.set(id, v)

	def set( self, id, value ):
		self._table[ id ] = value

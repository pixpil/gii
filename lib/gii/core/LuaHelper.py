def LuaCall( obj, name, *args ):
	f = obj[ name ]
	return f( obj, * args )

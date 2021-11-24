local function sendInput( ... )
	local host = mock.getGiiSyncHost()
	return host:tellConnectedPeers( 'remote_input', {...} )
end

--------------------------------------------------------------------
function onMouseDown( btn, x, y )
	return sendInput( 'm', 'down', 0,0, btn )
end

function onMouseUp( btn, x, y )
	return sendInput( 'm', 'up', 0,0, btn )
end

function onMouseMove( x, y )
	return sendInput( 'm', 'move', x,y, false )
end

function onMouseLeave()
	-- print()
end

function onMouseEnter()
	-- print()
end

function onMouseScroll( dx, dy, x, y )
	return sendInput( 'm', 'scroll', dx, dy, false )
end

--------------------------------------------------------------------
function onKeyDown( key )
	return sendInput( 'k', key, true )
end

function onKeyUp( key )
	return sendInput( 'k', key, false )
end

function onKeyChar( char )
	return sendInput( 'c', char )
end
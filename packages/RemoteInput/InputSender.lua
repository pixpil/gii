local activeTouches = {}
local touchBaseId = 4

function sendInput( ev, id, x,y,z )
	-- local tid = activeTouches[ id ]
	-- if not tid then
	-- 	tid = 1
	-- 	activeTouches[  ]
	-- if ev == 'ts' then
	-- end
	--TODO: use a simplified touch ID
	if ev == 'ts' then
		mock._sendTouchEvent( 'down', id, x,y  )
	elseif ev == 'tm' then
		mock._sendTouchEvent( 'move', id, x,y  )
	elseif ev == 'te' then
		mock._sendTouchEvent( 'up', id, x,y  )
	end
end

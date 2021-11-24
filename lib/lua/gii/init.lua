module( 'gii', package.seeall )
--------------------------------------------------------------------
--EDITOR MODULES
--------------------------------------------------------------------


require 'gii.SimpleClass'
require 'gii.bridge'
require 'gii.clidebugger'
require 'gii.debugger'

----------------------------
require 'gii.GIIRenderContext'
require 'gii.GIICanvasContext'

--------------------------------------------------------------------
-- MOAIGfxResourceMgr.setResourceLoadingPolicy( MOAIGfxResourceMgr.LOADING_POLICY_CPU_ASAP_GPU_NEXT )
-- MOAIGfxResourceMgr.setResourceLoadingPolicy( MOAIGfxResourceMgr.LOADING_POLICY_CPU_ASAP_GPU_BIND )
-- MOAIGfxResourceMgr.setResourceLoadingPolicy( MOAIGfxResourceMgr.LOADING_POLICY_CPU_GPU_ASAP )
-- MOAIGfxResourceMgr.setResourceLoadingPolicy( MOAIGfxResourceMgr.LOADING_POLICY_CPU_GPU_BIND )


function evalScript( src )
	local func, err = loadstring( src )
	if not func then
		print( 'failed load script' )
		print( err )
	else
		setfenv( func, setmetatable( {}, {__index=_G} ) )
		func()
	end
end

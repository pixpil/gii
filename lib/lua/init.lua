--------------------------------------------------------------------
--Env
--------------------------------------------------------------------
if jit then
	jit.off()
end
--[[
	PROJECT ENVIRONMENT VARIABLES
	* should be set by either editor or runtime launcher 
]]
-- GII_VERSION_MAJOR           = 0
-- GII_VERSION_MINOR           = 1
-- GII_VERSION_REV             = 0
-- GII_PROJECT_ASSET_PATH      = 'game/asset'
-- GII_PROJECT_SCRIPT_LIB_PATH = 'game/lib'
-- GII_PROJECT_ENV_LIB_PATH    = 'env/lib'


--------------------------------------------------------------------
--Setup package path
--------------------------------------------------------------------
package.path = package.path 
	.. ( ';' .. GII_PROJECT_SCRIPT_LIB_PATH .. '/?.lua' )
	.. ( ';' .. GII_PROJECT_SCRIPT_LIB_PATH .. '/?/init.lua' )
	.. ( ';' .. GII_PROJECT_ENV_LUA_PATH .. '/?.lua' )
	.. ( ';' .. GII_PROJECT_ENV_LUA_PATH .. '/?/init.lua' )
	.. ( ';' .. GII_LIB_LUA_PATH .. '/?.lua' )
	.. ( ';' .. GII_LIB_LUA_PATH .. '/?/init.lua' )

--------------------------------------------------------------------
function doRuntimeScript(name)
	local path = GII_DATA_PATH..'/lua/'..name
	return dofile(path)
end

--------------------------------------------------------------------
function lupaErrFunc( msg )
	return msg .. '\n' ..debug.traceback(2)
end

_collectgarbage = collectgarbage --keep a copy of original collectgarbage

python.seterrfunc( lupaErrFunc ) --lupa err func
--------------------------------------------------------------------
require 'gii'

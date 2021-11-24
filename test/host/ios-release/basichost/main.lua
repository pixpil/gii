--------------------------------------------------------------------
--Env
--------------------------------------------------------------------

GII_PROJECT_SCRIPT_LIB_PATH = 'lib'
GII_PROJECT_ASSET_PATH      = 'asset'

package.path = ''
	.. ( GII_PROJECT_SCRIPT_LIB_PATH .. '/?.lua' .. ';'  )
	.. ( GII_PROJECT_SCRIPT_LIB_PATH .. '/?/init.lua' .. ';'  )
	.. package.path

--------------------------------------------------------------------
--Runtimes
--------------------------------------------------------------------
if MOAIEnvironment.documentDirectory then
	MOAIFileSystem.setWorkingDirectory( MOAIEnvironment.documentDirectory .. '/game' )
end

require 'gamelib'
mock.setLogLevel( 'status' )
mock.TEXTURE_ASYNC_LOAD = true

--------------------------------------------------------------------
--Startup
--------------------------------------------------------------------
-- mock.init( 'game_config' )
-- mock.start()


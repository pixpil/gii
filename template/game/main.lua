if jit then
	jit.on()
end

GII_PROJECT_ASSET_PATH      = 'game/asset'
GII_PROJECT_SCRIPT_LIB_PATH = 'game/lib'
GII_PROJECT_SCRIPT_EXT_PATH = 'game/ext'

package.path = ''
	.. ( GII_PROJECT_SCRIPT_LIB_PATH .. '/?.lua' .. ';'  )
	.. ( GII_PROJECT_SCRIPT_LIB_PATH .. '/?/init.lua' .. ';'  )
	.. ( GII_PROJECT_SCRIPT_EXT_PATH .. '/?.lua' .. ';'  )
	.. ( GII_PROJECT_SCRIPT_EXT_PATH .. '/?/init.lua' .. ';'  )
	.. package.path

require 'gamelib'
require 'extlib'

GameModule.addGameModulePath( GII_PROJECT_ASSET_PATH .. '/?.lua' )
GameModule.addGameModulePath( GII_PROJECT_ASSET_PATH .. '/?/init.lua' )
-- mock.setLogLevel( 'status' )

mock.TEXTURE_ASYNC_LOAD = true
mock.TEXTURE_ASYNC_LOAD = false

--------------------------------------------------------------------
--Game Startup Config
--------------------------------------------------------------------
mock.setupEnvironment(
	false,
	'env/config/game'
)
mock.init( 'env/config/game_config.json' )
mock.start()

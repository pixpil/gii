GII_TESTING = true

GII_PROJECT_ASSET_PATH      = 'game/asset'
GII_PROJECT_SCRIPT_LIB_PATH = 'game/lib'
GII_PROJECT_SCRIPT_EXT_PATH = 'game/ext'

MOCK_PATH = GII_PROJECT_SCRIPT_LIB_PATH
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
-- mock.TEXTURE_ASYNC_LOAD = false
--------------------------------------------------------------------
--Game Startup Config
--------------------------------------------------------------------
mock.setupEnvironment(
	false,
	'env/config/game'
)
mock.init( 'env/config/game_config.json' )

--load workspace
local workspaceData   = mock.loadJSONFile( 'env/workspace/workspace.json') or {}

local previewingScene  = workspaceData[ 'scenegraph_editor/active_scene' ]
local sceneGroupFilter = workspaceData[ 'scene_group_filter_manager/current_filter' ]

if sceneGroupFilter then
	mock.setSceneGroupFilter( sceneGroupFilter['include'], sceneGroupFilter['exclude'] )
end

if previewingScene then
	mock.game:openSceneByPath( previewingScene )
	mock.game:start()
else
	os.exit()
end


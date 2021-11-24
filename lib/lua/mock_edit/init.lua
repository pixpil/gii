MOCK_ASYNC_RENDER_MODE = false

--------------------------------------------------------------------
--DEFAULT RUNTIME MODULES
--------------------------------------------------------------------
module( 'mock_edit', package.seeall )


require 'gamelib'
GameModule.addGameModulePath( GII_PROJECT_ASSET_PATH .. '/?.lua' )
GameModule.addGameModulePath( GII_PROJECT_ASSET_PATH .. '/?/init.lua' )


require 'mock'

--------------------------------------------------------------------
--CORE
--------------------------------------------------------------------
require 'mock_edit.common.signals'
require 'mock_edit.common.ModelHelper'
require 'mock_edit.common.CommonTools'
require 'mock_edit.common.AssetTools'
require 'mock_edit.common.EditorCommand'
require 'mock_edit.common.DeployTarget'
require 'mock_edit.common.bridge'
require 'mock_edit.common.utils'




--------------------------------------------------------------------
--EDITOR UI HELPER
--------------------------------------------------------------------
require 'mock_edit.UIHelper'


--------------------------------------------------------------------
--Editor related
--------------------------------------------------------------------
require 'mock_edit.EditorCanvas'


--------------------------------------------------------------------
--DEPLOY TARGETs
--------------------------------------------------------------------
require 'mock_edit.deploy.DeployTargetIOS'


--------------------------------------------------------------------
--Editor Related Res
--------------------------------------------------------------------
require 'mock_edit.common.resloader'


--------------------------------------------------------------------
require 'mock_edit.asset'



--------------------------------------------------------------------
--COMMON
--------------------------------------------------------------------
require 'mock_edit.env'

require 'mock_edit.commands'
require 'mock_edit.gizmos'
require 'mock_edit.EditorTools'
require 'mock_edit.manipulators'

require 'mock_edit.defaults'

require 'mock_edit.drag'



---------------------------------------------------------------------
--packages
require 'mock_edit.sqscript'
require 'mock_edit.animator'

require 'mock_edit.ShapeCanvas'
require 'mock_edit.ComponentPreview'


require 'mock_edit.tools'


--------------------------------------------------------------------
mock.TEXTURE_ASYNC_LOAD = false
-- MOAISim.getInputMgr().configuration = 'GII'
if MOAIInputMgr then
	MOAIInputMgr.configuration = 'GII'
else
	MOAISim.getInputMgr().configuration = 'GII'
end

io.stdout:setvbuf("line")

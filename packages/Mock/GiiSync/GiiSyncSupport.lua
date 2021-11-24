local pendingEntityModify = {}
local pendingEntityAdd    = {}
local pendingEntityRemove = {}
local pendingComponentAdd = {}
local pendingComponentRemove = {}

--------------------------------------------------------------------
function runScriptInGame( script )
	local host = mock.getGiiSyncHost()
	if host then
		host:tellConnectedPeers( 'command.run_script', script )
	end
end

--------------------------------------------------------------------
function openSceneFromGame()
	local host = mock.getGiiSyncHost()
	local function callback( peer, data )
		local sceneInfo = data and data[ 'scene.info' ]
		local path = sceneInfo and sceneInfo.path or false
		if not path then
			_warn( 'failed to query scene path' )
			return false
		end
		local sceneEditor = gii.app:getModule( 'scenegraph_editor' )
		return sceneEditor:openSceneByPath( path )
	end
	host:queryGame( 'scene.info', nil,  callback )
end

--------------------------------------------------------------------
function openSceneInGame()
	local host = mock.getGiiSyncHost()
	local path = game:getMainScene():getPath()
	if path then
		host:tellConnectedPeers( 'command.open_scene', path )
	else
		_warn( 'no main scene opened in editor.' )
	end
end

--------------------------------------------------------------------
function queryGame( keys, context, callback )
	local host = mock.getGiiSyncHost()
	if context then
		context = gii.dictToTable( context )
	end
	host:queryGame( keys, context, callback )
end

function updateOptions( options )
	local syncEntity = options[ 'syncEntity' ]
	if not syncEntity then
		pendingEntityModify = {}
	end
end

function notifyEntityModified( entity )
	if not entity then return end
	pendingEntityModify[ entity ] = true
end

function notifyEntityRemoved( entity )
	if not entity then return end
	pendingEntityRemove[ entity ] = true
end

function notifyEntityAdded( entity )
	if not entity then return end
	pendingEntityAdd[ entity ] = true
end

function notifyComponentRemoved( com, entity )
	pendingComponentRemove[ com ] = entity
end

function notifyComponentAdded( com, entity )
	pendingComponentAdd[ com ] = entity
end

function notifySceneChange()
	--clean entity
	pendingEntityModify = {}
end

function flushEntitySync()
	local host = mock.getGiiSyncHost()

	for entity in pairs( pendingEntityAdd ) do
		host:syncEntityChange( 'add', entity )
	end

	for entity in pairs( pendingEntityRemove ) do
		host:syncEntityChange( 'remove', entity )
	end

	for com, entity in pairs( pendingComponentAdd ) do
		host:syncEntityChange( 'com_add', entity, com )
	end

	for com, entity in pairs( pendingComponentRemove ) do
		host:syncEntityChange( 'com_remove', entity, com )
	end

	for entity in pairs( pendingEntityModify ) do
		host:syncEntityChange( 'modify', entity )
	end
	pendingEntityModify    = {}
	pendingEntityAdd       = {}
	pendingEntityRemove    = {}
	pendingComponentAdd    = {}
	pendingComponentRemove = {}
end

function isGameConnected()
	local host = mock.getGiiSyncHost()
	return host:isGameConnected()
end


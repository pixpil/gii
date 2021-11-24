local rawget,rawset= rawget,rawset

local bridge = GII_PYTHON_BRIDGE
module('gii',package.seeall)
_M.bridge = bridge

--------------------------------------------------------------------
-- CORE FUNCTIONS
--------------------------------------------------------------------

--communication
_M.emitPythonSignal     = bridge.emitPythonSignal
_M.emitPythonSignalNow  = bridge.emitPythonSignalNow
_M.connectPythonSignal  = bridge.connectPythonSignal
_M.registerPythonSignal = bridge.registerPythonSignal

--data
_M.sizeOfPythonObject   = bridge.sizeOfPythonObject
_M.newPythonDict        = bridge.newPythonDict
_M.newPythonList        = bridge.newPythonList
_M.appendPythonList     = bridge.appendPythonList
_M.deletePythonList     = bridge.deletePythonList
_M.newDict              = bridge.newDict
_M.getDict              = bridge.getDict
_M.setDict              = bridge.setDict
--other
_M.throwPythonException = bridge.throwPythonException
_M.getTime              = bridge.getTime
_M.generateGUID         = bridge.generateGUID

MOAIEnvironment.generateGUID = bridge.generateGUID

--import
_M.importPythonModule   = bridge.importModule

--asset
_M.getAssetNode         = bridge.getAssetNode

--gui
_M.getClipboard         = bridge.getClipboard
_M.setClipboard         = bridge.setClipboard

--data conversion
local encodeDict=bridge.encodeDict
local decodeDict=bridge.decodeDict

function tableToDict(table)
	local json = MOAIJsonParser.encode(table)
	return decodeDict(json)
end

function tableToDictPlain( t )
	local dict = newDict()
	for k,v in pairs( t ) do
		dict[ k ] = v
	end
	return dict
end

function tableToList(table)
	local list=bridge.newPythonList()
	for i, v in ipairs(table) do
		appendPythonList(list,v)
	end
	return list
end

function dictToTable(dict)
	local json = encodeDict(dict)
	return MOAIJsonParser.decode(json)
end

function dictToTablePlain(dict) --just one level?
	local t = {}
	for k in python.iter( dict ) do
		t[k] = dict[k]
	end
	return t	
end


local _sizeOf=sizeOfPythonObject
function listToTable(list)
	local c=_sizeOf(list)
	local r={}
	for i = 1, c do
		r[i]=list[i-1]
	end
	return r
end

function unpackPythonList( t )
	return unpack( listToTable( t ) )
end

--------------------------------------------------------------------
-- EDITOR RELATED
--------------------------------------------------------------------
function changeSelection( key, obj, ... )
	assert( type(key)=='string', 'selection key expected' )
	if obj then
		bridge.changeSelection( key, newPythonList(obj,...) )
	else
		bridge.changeSelection( key, nil )
	end
end

function addSelection( key, obj, ... )
	assert( type(key)=='string', 'selection key expected' )
	if obj then
		bridge.addSelection( key, newPythonList(obj,...) )
	else
		bridge.addSelection( key, nil )
	end
end

function removeSelection( key, obj, ... )
	assert( type(key)=='string', 'selection key expected' )
	if obj then
		bridge.removeSelection( key, newPythonList(obj,...) )
	else
		bridge.removeSelection( key, nil )
	end
end

function toggleSelection( key, obj, ... )
	assert( type(key)=='string', 'selection key expected' )
	if obj then
		bridge.toggleSelection( key, newPythonList(obj,...) )
	else
		bridge.toggleSelection( key, nil )
	end
end


function getSelection( key )
	assert( type(key)=='string', 'selection key expected' )
	return listToTable( bridge.getSelection( key ) )
end

-- Environment
-- getProjectExtPath = bridge.getProjectExtPath
-- getProjectPath    = bridge.getProjectPath
-- getAppPath        = bridge.getAppPath
app = bridge.app

function getProject()
	return app:getProject()
end

function getApp()
	return app
end

function getModule( id )
	return app:getModule( id )
end

function findDataFile( name )
	return app:findDataFile( name )
end

--------------------------------------------------------------------
-- PYTHON-LUA DELEGATION CREATION
--------------------------------------------------------------------
function loadLuaWithEnv(file, env, ...)
	if env then
		assert ( type( env ) == 'userdata' )
		env = dictToTablePlain( env )
	end

	env = setmetatable(env or {}, 
			{__index=function(t,k) return rawget(_G,k) end}
		)
	local func, err=loadfile(file)
	if not func then
		error('Failed load script:'..file..'\n'..err, 2)
	end
	
	env._M    = env

	setfenv(func, env)
	local args = {...}
	
	local function _f()
		return func( unpack( args ))
	end
	local function _onError( err, level )
		print ( err )
		print( debug.traceback( level or 2 ) )
		return err, level
	end

	local succ, err = xpcall( _f, _onError )
	if not succ then
		error('Failed start script:'.. file, 2)
	end

	local dir = env._path
	function env.dofile( path )

	end

	return env
end

function loadLuaDelegate( file, env, ... )
end

--------------------------------------------------------------------
-- Lua Functions For Python
--------------------------------------------------------------------
stepSim                 = assert( GIIHelper.stepSim )
setBufferSize           = assert( GIIHelper.setBufferSize )
local renderFrameBuffer = assert( GIIHelper.renderFrameBuffer ) --a manual renderer caller
manualDraw	            = assert( GIIHelper.draw	 )

local function _renderTable(t)
	for i,f in ipairs(t) do
		local tt=type(f)
		if tt=='table' then
			_renderTable(f)
		elseif tt=='userdata' then
			renderFrameBuffer(f)
		end
	end
end

renderTable = _renderTable

function updateNodeMgr()
	return MOAINodeMgr.update()
end

local collectgarbage = collectgarbage
function stepGC( stepSize )
	return collectgarbage( 'step', stepSize or 5 )
end

--------------------------------------------------------------------
-- Editor Command
--------------------------------------------------------------------
registerLuaEditorCommand = bridge.registerLuaEditorCommand
doCommand = bridge.doCommand
undoCommand = bridge.undoCommand

--------------------------------------------------------------------
-- MODEL
--------------------------------------------------------------------
local modelBridge = bridge.ModelBridge.get()

function registerModelProvider( setting )
	local priority  = setting.priority or 10
	local name      = setting.name
	local getTypeId           = assert( setting.getTypeId, 'getTypeId not provided' )
	local getModel            = assert( setting.getModel,  'getModel not provided' )
	local getModelFromTypeId  = assert( setting.getModelFromTypeId,  'getModelFromTypeId not provided' )
	return modelBridge:buildLuaObjectModelProvider( 
			name, priority, getTypeId, getModel, getModelFromTypeId
		)
end


function registerObjectEnumerator( setting )
	local name      = setting.name
	local enumerateObjects   = assert( setting.enumerateObjects, 'enumerateObjects not provided' )
	local getObjectRepr      = assert( setting.getObjectRepr, 'getObjectRepr not provided' )
	local getObjectTypeRepr  = assert( setting.getObjectTypeRepr, 'getObjectTypeRepr not provided' )
	return modelBridge:buildLuaObjectEnumerator(
			name,
			enumerateObjects,
			getObjectRepr,
			getObjectTypeRepr
		)
end


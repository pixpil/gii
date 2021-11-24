local findTopLevelEntities       = mock_edit.findTopLevelEntities
local getTopLevelEntitySelection = mock_edit.getTopLevelEntitySelection
local isEditorEntity             = mock_edit.isEditorEntity

local affirmGUID      = mock.affirmGUID
local reallocGUID     = mock.reallocGUID
local affirmSceneGUID = mock.affirmSceneGUID
local generateGUID = MOAIEnvironment.generateGUID

local firstRun = true

local function fixEntityPriority( e )
	for i, child in ipairs( e:getSortedChildrenList() ) do
		child:setPriority( i )
		fixEntityPriority( child )
	end
end

local function fixEntityGroupPriority( g )
	for child in pairs( g.childGroups ) do
		fixEntityGroupPriority( child )
	end
	for i, e in ipairs( g:getSortedEntityList() ) do
		e:setPriority( i )
		fixEntityPriority( e )
	end
end

local function fixScenePriority( scene )
	for _, group in pairs( scene:getRootGroups() ) do
		fixEntityGroupPriority( group )
	end
end


--------------------------------------------------------------------
CLASS:  SceneGraphEditor()

function SceneGraphEditor:__init()
	self.failedRefreshData = false
	self.previewState = false
	self.previousSceneGroupName = false
	connectSignalMethod( 'mainscene.open',  self, 'onMainSceneOpen' )
	connectSignalMethod( 'mainscene.close', self, 'onMainSceneClose' )
end

function SceneGraphEditor:getScene()
	return self.scene
end

function SceneGraphEditor:openScene( path )
	_stat( 'open mock scene', path )
	local scene = mock.game:openSceneByPathNow(
		path, 
		false,
		{
			fromEditor = true,
		},
		false
	) --dont start
	assert( scene )
	self.scene = scene
	mock_edit.setEditingScene( scene )
	affirmSceneGUID( scene )
	fixScenePriority( scene )
	self:postLoadScene()
	if firstRun then
		firstRun = false
	end
	self.previewState = false
	return scene
end

function SceneGraphEditor:postOpenScene()
	_stat( 'post open mock scene' )
	mock._doAssetCollection()
	mock.game:resetClock()
end

function SceneGraphEditor:closeScene()
	if not self.scene then return end
	_stat( 'close mock scene' )
	self:clearScene()
	mock_edit.setEditingScene( false )
	self.scene = false
	self.retainedSceneData = false
	self.retainedSceneSelection = false
	mock.game:resetClock()
end

function SceneGraphEditor:saveScene( path )
	local scene = self.scene
	if not scene then return false end
	for i, globalManager in ipairs( game.globalManagers ) do
		globalManager:preSceneSave( scene )
	end
	affirmSceneGUID( scene )
	local includeGroups = false
	local option = {
		keepProto = true;
		saveIndex = true;
	  includeGroups = includeGroups;
	}
	local result = mock.serializeSceneToFile( scene, path, option )
	for i, globalManager in ipairs( game.globalManagers ) do
		globalManager:onSceneSave( scene )
	end
	return result
end

function SceneGraphEditor:clearScene( keepEditorEntity )
	-- _collectgarbage( 'stop' )
	self.scene:clear( keepEditorEntity )
	self.scene:setEntityListener( false )
	-- _collectgarbage( 'restart' )
end

function SceneGraphEditor:refreshScene()
	local currentRootGroupName = self.scene:getDefaultRootGroup().name
	self:retainScene()
	self:clearScene( true )
	local succ = self:restoreScene()	
	self.scene:setDefaultRootGroup( self.scene:getRootGroup( currentRootGroupName ) )
	return succ
end

function SceneGraphEditor:getRootGroup( name )
	local scene = self.scene
	if not scene then return false end
	local group = scene:getRootGroup( name )
	return group
end


function SceneGraphEditor:getPreviousRootGroup()
	local scene = self.scene
	if not scene then return false end
	local group = scene:getRootGroup( self.previousSceneGroupName or nil )
	return group
end

function SceneGraphEditor:changeRootGroup( group )
	local scene = self.scene
	if not scene then return false end

	if group == scene:getDefaultRootGroup() then
		return 'same'
	end
	if not scene:setDefaultRootGroup( group ) then
		return false
	end
	local name = group.name
	self.previousSceneGroupName = name
	return true
end


function SceneGraphEditor:getAssetsInUse()
	if not self.scene then return false end
	local collected = mock.collectAssetFromScene( self.scene )
	return collected
end

local function collectFoldState( ent )
end

function SceneGraphEditor:saveEntityLockState()
	local output = {}
	for ent in pairs( self.scene.entities ) do
		if ent.__guid and ent._editLocked then output[ent.__guid] = true end
	end
	for group in pairs( self.scene:collectEntityGroups() ) do
		if ( not group._isRoot ) and group.__guid and group._editLocked then output[group.__guid] = true end
	end
	return gii.tableToDict( output )
end

function SceneGraphEditor:loadEntityLockState( data )
	local lockStates = gii.dictToTable( data )
	for ent in pairs( self.scene.entities ) do
		if ent.__guid and lockStates[ent.__guid] then
			ent:setEditLocked( true )
		end
	end
	for group in pairs( self.scene:collectEntityGroups() ) do
		if ( not group._isRoot ) and group.__guid and lockStates[group.__guid] then
			group:setEditLocked( true )
		end
	end
end

function SceneGraphEditor:saveIntrospectorFoldState()
	local output = {}
	for ent in pairs( self.scene.entities ) do
		if ent.__guid and ent.__foldState then output[ent.__guid] = true end
		for com in pairs( ent.components ) do
			if com.__guid and com.__foldState then output[com.__guid] = true end
		end
	end
	return gii.tableToDict( output )
end

function SceneGraphEditor:loadIntrospectorFoldState( containerFoldState )
	containerFoldState = gii.dictToTable( containerFoldState )
	for ent in pairs( self.scene.entities ) do
		if ent.__guid and containerFoldState[ent.__guid] then
			ent.__foldState = true
		end
		for com in pairs( ent.components ) do
			if com.__guid and containerFoldState[ com.__guid ] then
				com.__foldState = true
			end
		end

	end
end

function SceneGraphEditor:locateProto( path )
	local protoData = mock.loadAsset( path )
	local rootId = protoData.rootId
	return self:locateEntityByGUID( rootId )
end

function SceneGraphEditor:locateEntityByGUID( guid )
	for ent in pairs( self.scene.entities ) do
		if ent.__guid == guid then
			gii.changeSelection( 'scene', ent )
			return true
		end
	end
	return false
end

function SceneGraphEditor:postLoadScene()
	local scene = self.scene
	scene:setEntityListener( function( action, ... ) return self:onEntityEvent( action, ... ) end )
end


function SceneGraphEditor:startScenePreview()
	self.previewState = true
	-- _collectgarbage( 'collect' )
	MOAISim.forceGC()
	_stat( 'starting scene preview' )
	mock.game:start()
	_stat( 'scene preview started' )
end

function SceneGraphEditor:stopScenePreview()
	self.previewState = false
	_stat( 'stopping scene preview' )
	-- _collectgarbage( 'collect' )
	MOAISim.forceGC()
	mock.game:stop()
	--restore layer visiblity
	for i, l in pairs( mock.game:getLayers() ) do 
		l:setVisible( true )
	end
	_stat( 'scene preview stopped' )
end

function SceneGraphEditor:retainScene()
	if self.failedRefreshData then
		self.retainedSceneData = self.failedRefreshData
		self.failedRefreshData = false
		return
	end
	--keep current selection
	local guids = {}
	for i, e in ipairs( gii.getSelection( 'scene' ) ) do
		guids[ i ] = e.__guid
	end
	self.retainedSceneSelection = guids
	self.retainedSceneData = mock.serializeScene( self.scene, { keepProto = true } )
	--keep node fold state
end


function SceneGraphEditor:restoreScene()
	if not self.retainedSceneData then return true end
	local function _onError( msg )
		local errMsg = msg
		local tracebackMsg = debug.traceback(2)
		return errMsg .. '\n' .. tracebackMsg
	end
	self.scene:reset()
	local ok, msg = xpcall( function()
			mock.deserializeScene( self.retainedSceneData, self.scene )
		end,
		_onError
		)
	gii.emitPythonSignal( 'scene.update' )
	if ok then
		self.retainedSceneData = false
		self:postLoadScene()		
		_owner.tree:rebuild()
		local result = {}
		for i, guid in ipairs( self.retainedSceneSelection ) do
			local e = self:findEntityByGUID( guid )
			if e then table.insert( result, e ) end			
		end
		gii.changeSelection( 'scene', unpack( result ) )
		self.retainedSceneSelection = false		
		return true
	else
		print( msg )
		self.failedRefreshData = self.retainedSceneData
		return false
	end
end

function SceneGraphEditor:findEntityByGUID( id )
	local result = false
	for e in pairs( self.scene.entities ) do
		if e.__guid == id then
			result = e
		end
	end
	return result
end

function SceneGraphEditor:findComByGUID( id )
	local result = false
	for e in pairs( self.scene.entities ) do
		local com = e:getComponentByGUID( id )
		if com then
			result = com
		end
	end
	return result
end

local function collectEntity( e, typeId, collection )
	if isEditorEntity( e ) then return end
	if isInstance( e, typeId ) then
		collection[ e ] = true
	end
	for child in pairs( e.children ) do
		collectEntity( child, typeId, collection )
	end
end

local function collectComponent( entity, typeId, collection )
	if isEditorEntity( entity ) then return end
	for com in pairs( entity.components ) do
		if not com.FLAG_INTERNAL and isInstance( com, typeId ) then
			collection[ com ] = true
		end
	end
	for child in pairs( entity.children ) do
		collectComponent( child, typeId, collection )
	end
end

local function collectEntityGroup( group, collection )
	if isEditorEntity( group ) then return end
	collection[ group ] = true 
	for child in pairs( group.childGroups ) do
		collectEntityGroup( child, collection )
	end
end

function SceneGraphEditor:enumerateObjects( typeId, context, option )
	local scene = self.scene
	if not scene then return nil end
	local result = {}
	--REMOVE: demo codes
	if typeId == 'entity' then	
		local collection = {}	
		
		for e in pairs( scene.entities ) do
			collectEntity( e, mock.Entity, collection )
		end

		for e in pairs( collection ) do
			table.insert( result, e )
		end
	
	elseif typeId == 'group' then	
		local collection = {}	
		
		for g in pairs( scene:getRootGroup().childGroups ) do
			collectEntityGroup( g, collection )
		end

		for g in pairs( collection ) do
			table.insert( result, g )
		end

	elseif typeId == 'entity_in_group' then	
		local collection = {}	
		--TODO:!!!!
		
		for e in pairs( scene.entities ) do
			collectEntity( e, mock.Entity, collection )
		end

		for e in pairs( collection ) do
			table.insert( result, e )
		end

	else
		local collection = {}	
		if isSubclass( typeId, mock.Entity ) then
			for e in pairs( scene.entities ) do
				collectEntity( e, typeId, collection )
			end
		else
			for e in pairs( scene.entities ) do
				collectComponent( e, typeId, collection )
			end
		end
		for e in pairs( collection ) do
			table.insert( result, e )
		end
	end
	return result
end


function SceneGraphEditor:onEntityEvent( action, entity, com )
	if self.previewState then return end --ignore entity event on previewing
	
	emitSignal( 'scene.entity_event', self.scene, action, entity, com )
	
	if action == 'clear' then
		return gii.emitPythonSignal( 'scene.clear' )
	end

	if isEditorEntity( entity ) then return end

	if action == 'add' then
		_owner.addEntityNode( entity )
		-- gii.emitPythonSignal( 'scene.update' )
	elseif action == 'remove' then
		_owner.removeEntityNode( entity )
		-- gii.emitPythonSignal( 'scene.update' )
	elseif action == 'add_group' then
		_owner.addEntityGroupNode( entity )
		-- gii.emitPythonSignal( 'scene.update' )
	elseif action == 'remove_group' then
		_owner.removeEntityNode( entity )
		-- gii.emitPythonSignal( 'scene.update' )
	end

end

function SceneGraphEditor:getAssetInSelectedEntity()
	local contextEntity = gii.getSelection('scene')[1]
	if not isInstance( contextEntity, mock.Entity ) then return {} end
	local collected = mock.collectAssetFromEntity( contextEntity )
	local result = {}
	for assetPath in pairs( collected ) do
		table.insert( result, assetPath )
	end
	return result
end

function SceneGraphEditor:onMainSceneOpen( scn )
	gii.emitPythonSignal( 'scene.change' )
end

function SceneGraphEditor:onMainSceneClose( scn )
	gii.emitPythonSignal( 'scene.change' )
end

function SceneGraphEditor:makeSceneSelectionCopyData()
	local targets = getTopLevelEntitySelection()
	local dataList = {}
	for _, ent in ipairs( targets ) do
		if not ent:isInstance( mock.EntityGroup ) then
			local data = mock.makeEntityCopyData( ent )
			table.insert( dataList, data )
		end
	end
	return encodeJSON( { 
		entities = dataList,
		scene    = editor.scene.assetPath or '<unknown>',
	} )
end

function SceneGraphEditor:makeComponentCopyData( com )
	local data = mock.makeComponentCopyData( com )
	return encodeJSON( {
			data = data
		} )
end

editor = SceneGraphEditor()

--------------------------------------------------------------------
function enumerateSceneObjects( enumerator, typeId, context, option )
	--if context~='scene_editor' then return nil end
	return editor:enumerateObjects( typeId, context, option )
end

function getSceneObjectRepr( enumerator, obj )
	if isInstance( obj, mock.Entity ) then
		return obj:getFullName() or '<unnamed>'

	elseif isInstance( obj, mock.EntityGroup ) then
		return obj:getFullName() or '<unnamed>'

	end
	--todo: component
	local ent = obj._entity
	if ent then
		return ent:getFullName() or '<unnamed>'
	end
	return nil
end

function getSceneObjectTypeRepr( enumerator, obj )
	local class = getClass( obj )
	if class then
		return class.__name
	end
	return nil
end

gii.registerObjectEnumerator{
	name = 'scene_object_enumerator',
	enumerateObjects   = enumerateSceneObjects,
	getObjectRepr      = getSceneObjectRepr,
	getObjectTypeRepr  = getSceneObjectTypeRepr
}


--------------------------------------------------------------------
function enumerateLayers( enumerator, typeId, context )
	--if context~='scene_editor' then return nil end
	if typeId ~= 'layer' then return nil end
	local r = {}
	for i, l in ipairs( game.layers ) do
		if l.name ~= '_GII_EDITOR_LAYER' then
			table.insert( r, l.name )
		end
	end
	return r
end

function getLayerRepr( enumerator, obj )
	return obj
end

function getLayerTypeRepr( enumerator, obj )
	return 'Layer'
end

gii.registerObjectEnumerator{
	name = 'layer_enumerator',
	enumerateObjects   = enumerateLayers,
	getObjectRepr      = getLayerRepr,
	getObjectTypeRepr  = getLayerTypeRepr
}


--------------------------------------------------------------------
CLASS: CmdSelectScene ( mock_edit.EditorCommandNoHistory )
	:register( 'scene_editor/select_scene')


function CmdSelectScene:init( option )
	return gii.changeSelection( 'scene', editor.scene )
end
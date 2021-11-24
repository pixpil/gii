module 'mock_edit'
local findTopLevelEntities       = mock_edit.findTopLevelEntities
local getTopLevelEntitySelection = mock_edit.getTopLevelEntitySelection
local isEditorEntity             = mock_edit.isEditorEntity

local affirmGUID      = mock.affirmGUID
local reallocGUID     = mock.reallocGUID
local affirmSceneGUID = mock.affirmSceneGUID
local generateGUID = MOAIEnvironment.generateGUID

local function extractNumberPrefix( name )
	local numberPart = string.match( name, '_%d+$' )
	if numberPart then
		local mainPart = string.sub( name, 1, -1 - #numberPart )
		return mainPart, tonumber( numberPart )
	end
	return name, nil
end

local function findNextNumberProfix( scene, name )
	local max = -1
	local pattern = name .. '_(%d+)$'
	for ent in pairs( scene.entities ) do
		local n = ent:getName()
		if n then
			if n == name then 
				max = math.max( 0, max )
			else
				local id = string.match( n, pattern )
				if id then
					max = math.max( max, tonumber( id ) )
				end
			end
		end
	end
	return max
end

local function makeNumberProfix( scene, entity )
	local n = entity:getName()
	if n then
		--auto increase prefix
		local header, profix = extractNumberPrefix( n )
		local number = findNextNumberProfix( scene, header )
		if number >= 0 then
			local profix = '_' .. string.format( '%02d', number + 1 )
			entity:setName( header .. profix )
		end
	end
end

local function centerEntityInSceneView( entity )
	local sceneView = mock_edit.getCurrentSceneView()
	if sceneView then
		local x, y, z = sceneView:getCenter()
		GIIHelper.setWorldLoc( entity:getProp( 'physics' ), x, y, z )
	end
	return entity
end

--------------------------------------------------------------------
CLASS: CmdCreateEntityBase ( mock_edit.EditorCommand )
function CmdCreateEntityBase:init( option )
	local contextEntity 
	if option[ 'context_entity' ] then
		contextEntity = option[ 'context_entity' ]
	else
		contextEntity = gii.getSelection( 'scene' )[1]
	end
	if isInstance( contextEntity, mock.Entity ) then
		if option[ 'create_sibling' ] then
			self.parentEntity = contextEntity:getParent()
		else
			self.parentEntity = contextEntity
		end
	elseif isInstance( contextEntity, mock.EntityGroup ) then
		self.parentEntity = contextEntity
	else
		self.parentEntity = false
	end
	self.context = option[ 'context' ] or 'new'
end

function CmdCreateEntityBase:createEntity()
end

function CmdCreateEntityBase:getResult()
	return self.created
end

function CmdCreateEntityBase:processGUID( entity )
	affirmGUID( entity )
end

function CmdCreateEntityBase:redo()
	local entity = self:createEntity()
	if not entity then return false end
	self:processGUID( entity )
	self.created = entity
	if self.parentEntity then
		self.parentEntity:addChild( entity )
	else
		getEditingScene():addEntity( entity )
	end
	centerEntityInSceneView( entity )
	gii.emitPythonSignal( 'entity.added', self.created, self:getEntityCreationContext() )
end

function CmdCreateEntityBase:getEntityCreationContext()
	return self.context
end

function CmdCreateEntityBase:undo()
	self.created:destroyWithChildrenNow()
	gii.emitPythonSignal( 'entity.removed', self.created )
end

local function _editorInitCom( com )
	if com.onEditorInit then
		com:onEditorInit()
	end
end

local function _editorDeleteCom( com )
	if com.onEditorDelete then
		com:onEditorDelete()
	end
end

local function _editorDeleteEntity( e )
	if e.onEditorDelete then
		e:onEditorDelete()
	end
	for com in pairs( e.components ) do
		_editorDeleteCom( com )
	end
	for child in pairs( e.children ) do
		_editorDeleteEntity( child )
	end
end

local function _editorInitEntity( e )
	if e.onEditorInit then
		e:onEditorInit()
	end

	for com in pairs( e.components ) do
		_editorInitCom( com )
	end

	for child in pairs( e.children ) do
		_editorInitEntity( child )
	end
end

--------------------------------------------------------------------
CLASS: CmdAddEntity ( CmdCreateEntityBase )
	:register( 'scene_editor/add_entity' )

function CmdAddEntity:init( option )
	CmdCreateEntityBase.init( self, option )
	self.precreatedEntity = option.entity
	self.context          = option.context or 'new'
	if not self.precreatedEntity then
		return false
	end
	_editorInitEntity( self.precreatedEntity )
end

function CmdAddEntity:getEntityCreationContext()
	return self.context or 'new'
end

function CmdAddEntity:createEntity()
	return self.precreatedEntity
end

--------------------------------------------------------------------
CLASS: CmdCreateEntity ( CmdCreateEntityBase )
	:register( 'scene_editor/create_entity' )

function CmdCreateEntity:init( option )
	CmdCreateEntityBase.init( self, option )
	self.entityName = option.name
end

function CmdCreateEntity:createEntity()
	local e
	if ( not self.entityName ) or self.entityName == 'Empty' then
		e = CommonTools.createEmptyEntity( self.parentEntity )
	else
		local entType = mock.getEntityType( self.entityName )
		assert( entType )
		e = entType()
	end
	_editorInitEntity( e )
	if not e.name then e.name = self.entityName end
	return e
end

function CmdCreateEntity:undo()
	self.created:destroyWithChildrenNow()
	gii.emitPythonSignal('entity.removed', self.created )
end

--------------------------------------------------------------------
CLASS: CmdRemoveEntity ( mock_edit.EditorCommand )
	:register( 'scene_editor/remove_entity' )

function CmdRemoveEntity:init( option )
	local entities = option[ 'entities' ]
	if entities and type( entities ) ~= 'table' then
		entities = gii.listToTable( entities )
	end
	if not entities then
		entities = getTopLevelEntitySelection()
	end
	self.selection = entities
end

function CmdRemoveEntity:redo()
	--TODO: update ide in batch 
	local introspector = gii.getModule( 'introspector' )
	introspector:pauseUpdate( true )

	local removed = {}
	for _, target in ipairs( self.selection ) do
		if isInstance( target, mock.Entity ) then
			if target.scene then 
				removed[ target ] = true
				target:destroyWithChildrenNow()
			end
		elseif isInstance( target, mock.EntityGroup ) then
			removed[ target ] = true
			target:destroyWithChildrenNow()
		end
	end

	for target in pairs( removed ) do
		gii.emitPythonSignal('entity.removed', target )
	end
	introspector:pauseUpdate( false )
end

function CmdRemoveEntity:undo()
	--todo: RESTORE deleted
	-- gii.emitPythonSignal('entity.added', self.created )
end


--------------------------------------------------------------------
CLASS: CmdCloneEntity ( mock_edit.EditorCommand )
	:register( 'scene_editor/clone_entity' )

function CmdCloneEntity:init( option )
	local targets = getTopLevelEntitySelection()
	self.targets = targets
	self.created = false
	if not next( targets ) then return false end
end

function CmdCloneEntity:redo()
	local createdList = {}
	for _, target in ipairs( self.targets ) do
		if isInstance( target, mock.EntityGroup ) then
			mock_edit.alertMessage( 'todo', 'Group clone not yet implemented', 'info' )
			return false
		else
			local created = mock.copyAndPasteEntity( target, generateGUID )
			makeNumberProfix( getEditingScene(), created )
			local parent = target.parent
			affirmGUID( created )
			if parent then
				parent:addChild( created )
			else
				getEditingScene():addEntity( created, nil, target._entityGroup )
			end		
			table.insert( createdList, created )
			gii.emitPythonSignal( 'entity.added', created, 'clone' )
		end
	end
	gii.changeSelection( 'scene', unpack( createdList ) )
	self.createdList = createdList	
end

function CmdCloneEntity:undo()
	--todo:
	for i, created in ipairs( self.createdList ) do
		created:destroyWithChildrenNow()
		gii.emitPythonSignal( 'entity.removed', created )
	end
	self.createdList = false
end

--------------------------------------------------------------------
CLASS: CmdPasteEntity ( mock_edit.EditorCommand )
	:register( 'scene_editor/paste_entity' )

function CmdPasteEntity:init( option )
	self.data   = decodeJSON( option['data'] )
	self.pos    = option[ 'pos' ]
	local context = option[ 'context' ] or gii.getSelection( 'scene' )[1] or false
	if self.pos == 'sibling' then
		if context then
			self.parent = context:getParentOrGroup()
		else
			self.parent = false
		end
	else --into
		self.parent = context
	end
	self.createdList = false
	if not self.data then _error( 'invalid entity data' ) return false end
end

function CmdPasteEntity:redo()
	local createdList = {}
	local parent = self.parent
	for i, copyData in ipairs( self.data.entities ) do
		local entityData = mock.makeEntityPasteData( copyData, generateGUID )
		local created = mock.deserializeEntity( entityData )
		if parent then
			parent:addChild( created )
		else
			getEditingScene():addEntity( created )
		end		
		gii.emitPythonSignal('entity.added', created, 'paste' )
		table.insert( createdList, created )
		affirmGUID( created )
	end
	self.createdList = createdList
	gii.changeSelection( 'scene', unpack( createdList ) )
end

function CmdPasteEntity:undo()
	--todo:
	for i, created in ipairs( self.createdList ) do
		created:destroyWithChildrenNow()
		gii.emitPythonSignal('entity.removed', created )
	end
	self.createdList = false
end


--------------------------------------------------------------------
CLASS: CmdReparentEntity ( mock_edit.EditorCommand )
	:register( 'scene_editor/reparent_entity' )

function CmdReparentEntity:init( option )
	local mode = option[ 'mode' ] or 'child'
	if mode == 'sibling' then
		self.target   = option['target']:getParentOrGroup()
	else
		self.target   = option['target']
	end
	self.children = getTopLevelEntitySelection()
	self.oldParents = {}
	local targetIsEntity = isInstance( self.target, mock.Entity )
	for i, e in ipairs( self.children ) do
		if isInstance( e, mock.EntityGroup ) and targetIsEntity then
			mock_edit.alertMessage( 'fail', 'cannot make Group child of Entity', 'info' )
			return false
		end
	end
end

function CmdReparentEntity:redo()
	local target = self.target
	for i, e in ipairs( self.children ) do
		if isInstance( e, mock.Entity ) then
			self:reparentEntity( e, target )
		elseif isInstance( e, mock.EntityGroup ) then
			self:reparentEntityGroup( e, target )
		end
	end	
end

function CmdReparentEntity:reparentEntityGroup( group, target )
	local targetGroup = false
	if target == 'root' then
		targetGroup = getEditingScene():getRootGroup()

	elseif isInstance( target, mock.EntityGroup ) then
		targetGroup = target

	else
		error()		
	end

	group:reparent( targetGroup )
	gii.emitPythonSignal( 'entity.modified', group )
end


function CmdReparentEntity:reparentEntity( e, target )
	e:forceUpdate()
	local tx, ty ,tz = e:getWorldLoc()
	local px, py, pz = e:getPiv()
	tx = tx + px
	ty = ty + py
	tz = tz + pz
	local sx, sy ,sz = e:getWorldScl()
	local rz = e:getWorldRot()
	
	--TODO: world rotation X,Y	
	if target == 'root' then
		e:setLoc( tx, ty, tz )
		e:setScl( sx, sy, sz )
		e:setRotZ( rz )
		e:reparent( nil )
		e:reparentGroup( getEditingScene():getRootGroup() )

	elseif isInstance( target, mock.EntityGroup ) then
		e:setLoc( tx, ty, tz )
		e:setScl( sx, sy, sz )
		e:setRotZ( rz )
		e:reparent( nil )
		e:reparentGroup( target )

	else
		target:forceUpdate()
		local x, y, z = target:worldToModel( tx, ty, tz )
		
		local sx1, sy1, sz1 = target:getWorldScl()
		sx = ( sx1 == 0 ) and 0 or sx/sx1
		sy = ( sy1 == 0 ) and 0 or sy/sy1
		sz = ( sz1 == 0 ) and 0 or sz/sz1
		

		local rz1 = target:getWorldRot()
		rz = rz1 == 0 and 0 or rz/rz1
		e:setLoc( x, y, z )
		e:setScl( sx, sy, sz )
		e:setRotZ( rz )
		e:reparent( target )
	end

	gii.emitPythonSignal( 'entity.modified', e )

end


function CmdReparentEntity:undo()
	--todo:
	_error( 'NOT IMPLEMENTED' )
end

--------------------------------------------------------------------
local function reloadPrefabEntity( entity )
	local guid = entity.__guid
	local prefabPath = entity.__prefabId

	--Just recreate entity from prefab
	local prefab, node = mock.loadAsset( prefabPath )
	if not prefab then return false end
	local newEntity = prefab:createInstance()
	--only perserve location?
	newEntity:setLoc( entity:getLoc() )
	newEntity:setName( entity:getName() )
	newEntity:setLayer( entity:getLayer() )
	reallocGUID( newEntity )
	newEntity.__guid = guid
	newEntity.__prefabId = prefabPath
	local parent = entity:getParentOrGroup()
	entity:destroyWithChildrenNow()	

	if parent then
		parent:addChild( newEntity )
	end
	-- entity:addSibling( newEntity )
	-- _owner.addEntityNode( newEntity )

	return newEntity
end

--------------------------------------------------------------------
CLASS: CmdCreatePrefab ( mock_edit.EditorCommand )
	:register( 'scene_editor/create_prefab' )

function CmdCreatePrefab:init( option )
	self.prefabFile = option['file']
	self.prefabPath = option['prefab']
	self.entity     = option['entity']
end

function CmdCreatePrefab:redo()
	if mock.saveEntityToPrefab( self.entity, self.prefabFile ) then
		self.entity.__prefabId = self.prefabPath
		return true
	else
		return false
	end
end

--------------------------------------------------------------------
CLASS: CmdCreatePrefabInstance ( CmdCreateEntityBase )
	:register( 'scene_editor/create_prefab_instance' )

function CmdCreatePrefabInstance:init( option )
	CmdCreateEntityBase.init( self, option )
	self.prefabPath = option['prefab']
end

function CmdCreatePrefabInstance:createEntity()
	local prefab, node = mock.loadAsset( self.prefabPath )
	if not prefab then return false end
	local instance = prefab:createInstance()

	return instance
end

function CmdCreatePrefabInstance:processGUID( entity )
	reallocGUID( entity )
end

function CmdCreatePrefabInstance:getEntityCreationContext()
	return 'instance'
end

--------------------------------------------------------------------
CLASS: CmdUnlinkPrefab ( mock_edit.EditorCommand )
	:register( 'scene_editor/unlink_prefab' )

function CmdUnlinkPrefab:init( option )
	self.entity     = option['entity']
	self.prefabId = self.entity.__prefabId
end

function CmdUnlinkPrefab:redo()
	self.entity.__prefabId = nil
	gii.emitPythonSignal( 'prefab.unlink', self.entity )
end

function CmdUnlinkPrefab:undo()
	self.entity.__prefabId = self.prefabId --TODO: other process
	gii.emitPythonSignal( 'prefab.relink', self.entity )
end


--------------------------------------------------------------------
CLASS: CmdPushPrefab ( mock_edit.EditorCommand )
	:register( 'scene_editor/push_prefab' )

function CmdPushPrefab:init( option )
	self.entity     = option['entity']
end

function CmdPushPrefab:redo()
	local entity = self.entity
	local prefabPath = entity.__prefabId
	local node = mock.getAssetNode( prefabPath )
	local filePath = node:getAbsObjectFile( 'def' )
	if mock.saveEntityToPrefab( entity, filePath ) then
		gii.emitPythonSignal( 'prefab.push', entity )
		--Update all entity in current scene
		-- local scene = entity.scene
		-- local toReload = {}
		-- for e in pairs( scene.entities ) do
		-- 	if e.__prefabId == prefabPath and e~=entity then
		-- 		toReload[ e ] = true
		-- 	end
		-- end
		-- for e in pairs( toReload ) do
		-- 	reloadPrefabEntity( e )
		-- end
	else
		return false
	end
end

--------------------------------------------------------------------
CLASS: CmdPullPrefab ( mock_edit.EditorCommand )
	:register( 'scene_editor/pull_prefab' )

function CmdPullPrefab:init( option )
	self.entity     = option['entity']
end

function CmdPullPrefab:redo()
	self.newEntity = reloadPrefabEntity( self.entity )
	gii.emitPythonSignal( 'prefab.pull', self.newEntity )
	--TODO: reselect it ?
end

function CmdPullPrefab:undo()
	--TODO...
end

--------------------------------------------------------------------
CLASS: CmdCreatePrefabContainer ( CmdCreateEntityBase )
	:register( 'scene_editor/create_prefab_container' )

function CmdCreatePrefabContainer:init( option )
	CmdCreateEntityBase.init( self, option )
	self.prefabPath = option['prefab']
end

function CmdCreatePrefabContainer:createEntity()
	local container = mock.PrefabContainer()
	container:setPrefab( self.prefabPath )
	return container	
end

--------------------------------------------------------------------
CLASS: CmdMakeProto ( mock_edit.EditorCommand )
	:register( 'scene_editor/make_proto' )

function CmdMakeProto:init( option )
	self.entity = option['entity']
end

function CmdMakeProto:redo()
	self.entity.FLAG_PROTO_SOURCE = true
end

function CmdMakeProto:undo()
	self.entity.FLAG_PROTO_SOURCE = false
end


--------------------------------------------------------------------
CLASS: CmdCreateProtoInstance ( CmdCreateEntityBase )
	:register( 'scene_editor/create_proto_instance' )

function CmdCreateProtoInstance:init( option )
	CmdCreateEntityBase.init( self, option )
	self.protoPath = option['proto']
	self.ptype = mock.getAssetType( self.protoPath )
	if self.ptype ~= 'proto' and self.ptype ~= 'prefab' then
		_error( 'unkown prefab/proto type', self.protoPath )
		return false
	end
end

function CmdCreateProtoInstance:createEntity()
	if self.ptype == 'proto' then
		local proto = mock.loadAsset( self.protoPath )
		local id    = generateGUID()
		local instance = proto:createInstance( nil, id )
		instance.__overrided_fields = {
			[ 'loc' ] = true,
			[ 'name' ] = true,
		}
		makeNumberProfix( getEditingScene(), instance )
		return instance

	elseif self.ptype == 'prefab' then
		local prefab, node = mock.loadAsset( self.protoPath )
		if not prefab then return false end
		local instance = prefab:createInstance()
		makeNumberProfix( getEditingScene(), instance )
		return instance
	end

end

function CmdCreateProtoInstance:processGUID( entity )
	if self.ptype == 'prefab' then
		reallocGUID( entity )
	else
		affirmGUID( entity )
	end
end


function CmdCreateProtoInstance:getEntityCreationContext()
	return 'instance'
end

--------------------------------------------------------------------
CLASS: CmdCreateProtoContainer ( CmdCreateEntityBase )
	:register( 'scene_editor/create_proto_container' )

function CmdCreateProtoContainer:init( option )
	CmdCreateEntityBase.init( self, option )
	self.protoPath = option['proto']
	self.ptype = mock.getAssetType( self.protoPath )
	if self.ptype ~= 'proto' and self.ptype ~= 'prefab' then
		_error( 'unkown prefab/proto type', self.protoPath )
		return false
	end
end

function CmdCreateProtoContainer:createEntity()
	if self.ptype == 'proto' then
		local proto = mock.loadAsset( self.protoPath )
		local name = proto:getRootName()
		local container = mock.ProtoContainer()
		container:setName( name )
		container.proto = self.protoPath
		makeNumberProfix( getEditingScene(), container )
		return container
	else
		local prefab = mock.loadAsset( self.protoPath )
		local name = prefab:getRootName()
		local container = mock.PrefabContainer()
		container:setName( name )
		container.prefab = self.protoPath
		makeNumberProfix( getEditingScene(), container )
		return container
	end
end

--------------------------------------------------------------------
CLASS: CmdUnlinkProto ( mock_edit.EditorCommand )
	:register( 'scene_editor/unlink_proto' )

function CmdUnlinkProto:_retainAndClearComponentProtoState( entity, data )
	for com in pairs( entity.components ) do
		if com.__proto_history then
			data[ com ] = {
				overrided = com.__overrided_fields,
				history   = com.__proto_history,
			}
			com.__overrided_fields = nil
			com.__proto_history = nil
		end
	end
end

function CmdUnlinkProto:_retainAndClearChildProtoState( entity, data )
	if entity.PROTO_INSTANCE_STATE then return end
	if not entity.__proto_history then return end
	data[ entity ] = {
		overrided = entity.__overrided_fields,
		history   = entity.__proto_history,
	}
	entity.__overrided_fields = nil
	entity.__proto_history = nil
	self:_retainAndClearComponentProtoState( entity, data )
	for child in pairs( entity.children ) do
		self:_retainAndClearChildProtoState( child, data )
	end
end

function CmdUnlinkProto:_retainAndClearEntityProtoState( root, data )
	data = data or {}
	if root.PROTO_INSTANCE_STATE then
		data[ root ] = {
			overrided = root.__overrided_fields,
			history   = root.__proto_history,
			state     = root.PROTO_INSTANCE_STATE
		}
		for child in pairs( root.children ) do
			self:_retainAndClearChildProtoState( child, data )
		end
		self:_retainAndClearComponentProtoState( root, data )
		root.__overrided_fields   = nil
		root.__proto_history      = nil
		root.PROTO_INSTANCE_STATE = nil
	end
	return data
end

function CmdUnlinkProto:_restoreEntityProtoState( root, data )
	for ent, retained in pairs( data ) do
		if retained.state then
			ent.PROTO_INSTANCE_STATE = retained.state
		end
		ent.__overrided_fields = retained.overrided
		ent.__proto_history = retained.history
	end
end
--TODO
function CmdUnlinkProto:init( option )
	self.entity     = option['entity']
end

function CmdUnlinkProto:redo()	
	self.retainedState =  self:_retainAndClearEntityProtoState( self.entity )
	gii.emitPythonSignal( 'proto.unlink', self.entity )
	gii.emitPythonSignal( 'entity.modified', self.entity )
end

function CmdUnlinkProto:undo()
	self:_restoreEntityProtoState( self.retainedState )
	gii.emitPythonSignal( 'proto.relink', self.entity )
	gii.emitPythonSignal( 'entity.modified', self.entity )
end


--------------------------------------------------------------------
CLASS: CmdAssignEntityLayer ( mock_edit.EditorCommand )
	:register( 'scene_editor/assign_layer' )

function CmdAssignEntityLayer:init( option )
	self.layerName = option['target']
	self.entities  = gii.getSelection( 'scene' )	
	self.oldLayers = {}
end

function CmdAssignEntityLayer:redo()
	local layerName = self.layerName
	local oldLayers = self.oldLayers
	for i, e in ipairs( self.entities ) do
		oldLayers[ e ] = e:getLayer()
		e:setLayer( layerName )
		gii.emitPythonSignal( 'entity.renamed', e, '' )
	end	
end

function CmdAssignEntityLayer:undo()
	local oldLayers = self.oldLayers
	for i, e in ipairs( self.entities ) do
		layerName = oldLayers[ e ]
		e:setLayer( layerName )
		gii.emitPythonSignal( 'entity.renamed', e, '' )
	end	
end

--------------------------------------------------------------------
CLASS: CmdToggleEntityVisibility ( mock_edit.EditorCommand )
	:register( 'scene_editor/toggle_entity_visibility' )

function CmdToggleEntityVisibility:init( option )
	local target = option[ 'target' ]
	if target then
		self.entities = { target }
	else
		self.entities  = gii.getSelection( 'scene' )
	end
	self.originalVis  = {}
end

function CmdToggleEntityVisibility:redo()
	local vis = false
	local originalVis = self.originalVis
	for i, e in ipairs( self.entities ) do
		originalVis[ e ] = e:isLocalVisible()
		if e:isLocalVisible() then vis = true end
	end	
	vis = not vis
	for i, e in ipairs( self.entities ) do
		e:setVisible( vis )
		mock.markProtoInstanceOverrided( e, 'visible' )
		e:forceUpdate()
		gii.emitPythonSignal( 'entity.visible_changed', e )
		gii.emitPythonSignal( 'entity.modified', e, '' )
	end
end

function CmdToggleEntityVisibility:undo()
	local originalVis = self.originalVis
	for i, e in ipairs( self.entities ) do
		e:setVisible( originalVis[ e ] )
		e:forceUpdate()
		gii.emitPythonSignal( 'entity.modified', e, '' )
	end	
	self.originalVis  = {}
end



--------------------------------------------------------------------
CLASS: CmdToggleEntityGroupSolo ( mock_edit.EditorCommand )
	:register( 'scene_editor/toggle_entity_group_solo' )

function CmdToggleEntityGroupSolo:init( option )
	local target = option[ 'target' ]
	if target then
		self.entities = { target }
	else
		self.entities  = gii.getSelection( 'scene' )
	end
	-- self.originalVis  = {}
end

function CmdToggleEntityGroupSolo:redo()
	_error( 'TODO' )
end

function CmdToggleEntityGroupSolo:undo()
	--TODO
	_error( 'TODO' )
end


--------------------------------------------------------------------
CLASS: CmdToggleEntityLock ( mock_edit.EditorCommandNoHistory )
	:register( 'scene_editor/toggle_entity_lock' )

function CmdToggleEntityLock:init( option )
	local target = option[ 'target' ]
	if target then
		self.entities = { target }
	else
		self.entities  = gii.getSelection( 'scene' )
	end

	local locked = false
	for i, e in ipairs( self.entities ) do
		if e:isLocalEditLocked() then locked = true break end
	end	
	locked = not locked
	for i, e in ipairs( self.entities ) do
		e:setEditLocked( locked )
		gii.emitPythonSignal( 'entity.visible_changed', e )
		gii.emitPythonSignal( 'entity.modified', e, '' )
	end
end

--------------------------------------------------------------------
CLASS: CmdUnifyChildrenLayer ( mock_edit.EditorCommand )
	:register( 'scene_editor/unify_children_layer' )

function CmdUnifyChildrenLayer:init( option )
	--TODO
end

function CmdUnifyChildrenLayer:redo( )
	--TODO
end

function CmdUnifyChildrenLayer:undo( )
	--TODO
end

--------------------------------------------------------------------
CLASS: CmdFreezePivot ( mock_edit.EditorCommand )
	:register( 'scene_editor/freeze_entity_pivot' )

function CmdFreezePivot:init( option )
	self.entities  = gii.getSelection( 'scene' )
	self.previousPivots = {}
end

function CmdFreezePivot:redo( )
	local pivots = self.previousPivots
	for i, e in ipairs( self.entities ) do
		local px, py, pz = e:getPiv()
		e:setPiv( 0,0,0 )
		e:addLoc( -px, -py, -pz )
		-- for child in pairs( e:getChildren() ) do
		-- 	child:addLoc( -px, -py, -pz )
		-- end
		gii.emitPythonSignal( 'entity.modified', e, '' )
	end
end

function CmdFreezePivot:undo( )
	--TODO
end



--------------------------------------------------------------------
CLASS: CmdResetGroupLoc ( mock_edit.EditorCommand )
	:register( 'scene_editor/reset_group_loc' )

function CmdResetGroupLoc:init( option )
	self.selection = getTopLevelEntitySelection()
	self.prevTrans = {}
end

function CmdResetGroupLoc:redo()
	for i, e in ipairs( self.selection ) do
		self:resetGroupLoc( e )
	end
end

function CmdResetGroupLoc:resetGroupLoc( e )
	local x, y, z = e:getLoc()
	local px, py, pz = e:getPiv()
	self.prevTrans[ e ] = { x,y,z, px,py,pz }
	local dx, dy, dz = x - px, y - py, z - pz
	for child in pairs( e:getChildren() ) do
		child:addLoc( dx, dy, dz )
	end
	e:setLoc( 0,0,0 )
	e:setPiv( 0,0,0 )
	gii.emitPythonSignal( 'entity.modified', e, '' )
end

function CmdResetGroupLoc:undo( )
	for i, e in ipairs( self.selection ) do
		self:undoResetGroupLoc( e )
	end
end

function CmdResetGroupLoc:undoResetGroupLoc( e )
	local x,y,z, px,py,pz = unpack( self.prevTrans[ e ] )
	local dx, dy, dz = x - px, y - py, z - pz
	for child in pairs( e:getChildren() ) do
		child:addLoc( -dx, -dy, -dz )
	end
	e:setLoc( x, y, z )
	e:setPiv( px, py, pz )
	gii.emitPythonSignal( 'entity.modified', e, '' )
end




--------------------------------------------------------------------
CLASS: CmdEntityGroupCreate ( mock_edit.EditorCommand )
	:register( 'scene_editor/entity_group_create')


function CmdEntityGroupCreate:init( option )
	local contextEntity = gii.getSelection( 'scene' )[1]
	
	if isInstance( contextEntity, mock.Entity ) then
		if not contextEntity._entityGroup then
			mock_edit.alertMessage( 'fail', 'cannot create Group inside Entity', 'info' )
			return false
		end
		self.parentGroup = contextEntity._entityGroup
	elseif isInstance( contextEntity, mock.EntityGroup ) then
		self.parentGroup = contextEntity
	else
		self.parentGroup = getEditingScene():getRootGroup()
	end

	self.guid = generateGUID()

end

function CmdEntityGroupCreate:redo()
	self.createdGroup = mock.EntityGroup()
	self.parentGroup:addChildGroup( self.createdGroup )
	self.createdGroup.__guid = self.guid
	gii.emitPythonSignal( 'entity.added', self.createdGroup, 'new' )
end

function CmdEntityGroupCreate:undo()
	--TODO
	self.parentGroup:removeChildGroup( self.createdGroup )
end

function CmdEntityGroupCreate:getResult()
	return self.createdGroup
end


--------------------------------------------------------------------
CLASS: CmdGroupEntities ( mock_edit.EditorCommand )
	:register( 'scene_editor/group_entities')

function CmdGroupEntities:init( option )
	--TODO:!!!
	local contextEntity = gii.getSelection( 'scene' )[1]
	if isInstance( contextEntity, mock.Entity ) then
		if not contextEntity._entityGroup then
			mock_edit.alertMessage( 'fail', 'cannot create Group inside Entity', 'info' )
			return false
		end
		self.parentGroup = contextEntity._entityGroup
	elseif isInstance( contextEntity, mock.EntityGroup ) then
		self.parentGroup = contextEntity
	else
		self.parentGroup = getEditingScene():getRootGroup()
	end

	self.guid = generateGUID()

end

function CmdGroupEntities:redo()
	self.createdGroup = mock.EntityGroup()
	self.parentGroup:addChildGroup( self.createdGroup )
	self.createdGroup.__guid = self.guid
	gii.emitPythonSignal( 'entity.added', self.createdGroup, 'new' )
end

function CmdGroupEntities:undo()
	--TODO
	self.parentGroup:removeChildGroup( self.createdGroup )
end


--------------------------------------------------------------------
CLASS: CmdCreateComponent ( mock_edit.EditorCommand )
	:register( 'scene_editor/create_component' )

function CmdCreateComponent:init( option )
	self.componentName = option.name	
	local target
	target = option.target or gii.getSelection( 'scene' )[1]
	if not isInstance( target, mock.Entity ) then
		_warn( 'attempt to attach component to non Entity object', target:getClassName() )
		return false
	end	
	self.targetEntity  = target
end

function CmdCreateComponent:redo()	
	local comType = mock.getComponentType( self.componentName )
	assert( comType )
	local component = comType()
	-- if not component:isAttachable( self.targetEntity ) then
	-- 	mock_edit.alertMessage( 'todo', 'Group clone not yet implemented', 'info' )
	-- 	return false
	-- end
	component.__guid = generateGUID()
	self.createdComponent = component
	self.targetEntity:attach( component )
	if component.onEditorInit then
		component:onEditorInit()
	end
	gii.emitPythonSignal( 'component.added', component, self.targetEntity )	
end

function CmdCreateComponent:undo()
	self.targetEntity:detach( self.createdComponent )
	gii.emitPythonSignal( 'component.removed', component, self.targetEntity )	
end

--------------------------------------------------------------------
CLASS: CmdRemoveComponent ( mock_edit.EditorCommand )
	:register( 'scene_editor/remove_component' )

function CmdRemoveComponent:init( option )
	self.target = option['target']
end

function CmdRemoveComponent:redo()
	--todo
	local ent = self.target._entity
	if ent then
		ent:detach( self.target )
	end
	self.previousParent = ent
	gii.emitPythonSignal( 'component.removed', self.target, self.previousParent )	
end

function CmdRemoveComponent:undo()
	self.previousParent:attach( self.target )
	gii.emitPythonSignal( 'component.added', self.target, self.previousParent )	
end


--------------------------------------------------------------------
CLASS: CmdRenameEntity ( mock_edit.EditorCommand )
	:register( 'scene_editor/rename_entity' )

function CmdRenameEntity:init( option )
	self.target = option['target']
	self.newName = option['name']
	self.prevName = self.target:getName()
	self.prevOverrided = mock.isProtoInstanceOverrided( self.target, 'name' )
end

function CmdRenameEntity:redo()
	self.target:setName( self.newName )
	gii.emitPythonSignal( 'entity.renamed', self.target, self.newName )
	mock.markProtoInstanceOverrided( self.target, 'name' )
end

function CmdRenameEntity:undo()
	self.target:setName( self.prevName )
	gii.emitPythonSignal( 'entity.renamed', self.target, self.prevName )
	if not self.prevOverrided then
		mock.markProtoInstanceOverrided( self.target, 'name', false )
	end
end


--------------------------------------------------------------------
CLASS: CmdRenameComponent ( mock_edit.EditorCommand )
	:register( 'scene_editor/rename_component' )

function CmdRenameComponent:init( option )
	self.target = option['target']
	self.newAlias = option['alias']
	self.prevAlias = self.target._alias
end

function CmdRenameComponent:redo()
	self.target._alias = self.newAlias
	gii.emitPythonSignal( 'component.renamed', self.target, self.target._entity )
end

function CmdRenameComponent:undo()
	self.target._alias = self.prevAlias
	gii.emitPythonSignal( 'component.renamed', self.target, self.target._entity )
end

--------------------------------------------------------------------
CLASS: CmdPasteComponent( mock_edit.EditorCommand )
	:register( 'scene_editor/paste_component' )

function CmdPasteComponent:init( option )
	self.data   = decodeJSON( option['data'] )
	self.targetEntity = option[ 'entity' ] or gii.getSelection( 'scene' )[1] or false
	self.before = option[ 'before' ] or false
	if not self.data then _error( 'invalid entity data' ) return false end
	if not self.targetEntity then _error( 'no entity specified' ) return false end
end

function CmdPasteComponent:redo()
	local com = mock.deserialize( nil, self.data[ 'data' ] )
	if not com then return false end
	com.__guid = generateGUID()
	self.targetEntity:attach( com )
	self.created = com
	if self.before then
		local comList = self.targetEntity:getSortedComponentList()
		local idxAdded = table.index( comList, self.created )
		table.remove( comList, idxAdded )
		local idxTarget = table.index( comList, self.before )
		table.insert( comList, idxTarget, self.created )
		for i, com in ipairs( comList ) do
			com._componentID = i
		end
	end
	gii.emitPythonSignal( 'component.added', self.created, self.targetEntity )	
end

function CmdCreateComponent:undo()
	self.targetEntity:detach( self.createdComponent )
	gii.emitPythonSignal( 'component.removed', self.created, self.targetEntity )	
end

function CmdPasteComponent:undo()
	self.targetEntity:detach( self.created )
end

function CmdPasteComponent:getResult()
	return self.created
end


--------------------------------------------------------------------
CLASS: CmdChangeComponenOrder ( mock_edit.EditorCommand )
	:register( 'scene_editor/change_component_order' )

function CmdChangeComponenOrder:init( option )
	self.target = option[ 'target' ]
	self.delta = option[ 'delta' ]
	self.oldList = false
end

function CmdChangeComponenOrder:redo()
	self.target._alias = self.newAlias
	local ent = self.target._entity
	local comList = ent:getSortedComponentList()
	self.oldList = table.simplecopy( comList )
	local count = #comList
	local idx = table.index( comList, self.target )
	local newIdx
	local delta = self.delta
	if delta > 0 then --move down
		if newIdx == count then return false end
		newIdx = idx + 1
	elseif delta < 0 then
		if newIdx == 1 then return false end
		newIdx = idx - 1
	end
	table.swap( comList, newIdx, idx )
	for i, com in ipairs( comList ) do
		com._componentID = i
	end
	gii.emitPythonSignal( 'component.reordered', self.target, self.target._entity )
end

function CmdChangeComponenOrder:undo()
	for i, c in ipairs( self.oldList ) do
		c._componentID = i
	end
	self.oldList = false
	gii.emitPythonSignal( 'component.reordered', self.target, self.target._entity )
end


--------------------------------------------------------------------
CLASS: CmdRenameRootGroup ( mock_edit.EditorCommand )
	:register( 'scene_editor/rename_root_group' )

function CmdRenameRootGroup:init( option )
	self.target   = option['group']
	self.newName  = option['name']
	self.prevName = self.target:getName()
end

function CmdRenameRootGroup:redo()
	self.target:setName( self.newName )
	gii.emitPythonSignal( 'root_group.renamed', self.target, self.newName )
end

function CmdRenameRootGroup:undo()
	self.target:setName( self.prevName )
	gii.emitPythonSignal( 'root_group.renamed', self.target, self.prevName )
end



--------------------------------------------------------------------
CLASS: CmdCreateRootGroup ( mock_edit.EditorCommand )
	:register( 'scene_editor/create_root_group' )

function CmdCreateRootGroup:init( option )
	local name = option['name']
	if not name or name == '' then return false end
	self.name  = name
	self.createdGroup = false
	local scn = getEditingScene()
	if scn:getRootGroup( name ) then return false end
	self.guid = generateGUID()
end

function CmdCreateRootGroup:redo()
	self.createdGroup = getEditingScene():addRootGroup( self.name )
	self.createdGroup.__guid = self.guid
	gii.emitPythonSignal( 'root_group.added', self.createdGroup )
end

function CmdCreateRootGroup:undo()
	getEditingScene():removeRootGroup( self.createdGroup )
	gii.emitPythonSignal( 'root_group.removed', self.createdGroup )
end

function CmdCreateRootGroup:getResult()
	return self.createdGroup
end


--------------------------------------------------------------------
CLASS: CmdRemoveRootGroup ( mock_edit.EditorCommand )
	:register( 'scene_editor/remove_root_group' )

function CmdRemoveRootGroup:init( option )
	self.targetGroup = option[ 'group' ]
	self.guid = self.targetGroup.__guid
	self.name = self.targetGroup:getName()
end

function CmdRemoveRootGroup:redo()
	getEditingScene():removeRootGroup( self.targetGroup )
	gii.emitPythonSignal( 'root_group.removed', self.targetGroup )
	self.targetGroup = false
end

function CmdRemoveRootGroup:undo()
	self.targetGroup = getEditingScene():addRootGroup( self.name )
	self.targetGroup.__guid = self.guid
	self.targetGroup:setName( self.name )
	gii.emitPythonSignal( 'root_group.added', self.targetGroup )
end



--------------------------------------------------------------------
CLASS: CmdReplaceEntityClass ( mock_edit.EditorCommand )
	:register( 'scene_editor/replace_entity_class' )

function CmdReplaceEntityClass:init( option )
	self.targetClass = option[ 'targetClass' ]
	-- self.targetEntityData = 
	self.targetEntity = gii.getSelection( 'scene' )[1]
end

function CmdReplaceEntityClass:redo()
	local entityData = mock.makeEntityPasteData( copyData, generateGUID )
	
end

function CmdReplaceEntityClass:undo()
	--TODO
end


--------------------------------------------------------------------
CLASS: CmdReallocateSceneGUID ( mock_edit.EditorCommand )
	:register( 'scene_editor/reallocate_scene_guid' )

function CmdReallocateSceneGUID:init()
end

function CmdReallocateSceneGUID:redo()
	local sceneView = mock_edit.getCurrentSceneView()
	local scene = sceneView:getScene()
	for group in pairs( scene:collectEntityGroups() ) do
		group.__guid = generateGUID()
		for e in pairs( group.entities ) do
			if not ( e.FLAG_INTERNAL or e.FLAG_EDITOR_OBJECT ) and not e.parent then
				reallocGUID( e )
			end
		end
	end
end

--------------------------------------------------------------------
CLASS: CmdSetBypassed ( mock_edit.EditorCommand )
	:register( 'scene_editor/set_bypassed' )

function CmdSetBypassed:init( option )
	self.target = option[ 'target' ]
	self.value  = option[ 'value' ]
	self.value0 = self.target.FLAG_BYPASSED and true or false
end

function CmdSetBypassed:redo()
	self.target.FLAG_BYPASSED = self.value
	if self.target:isInstance( mock.Entity ) then
		gii.emitPythonSignal( 'entity.modified', self.target )
	else
		local ent = self.target._entity
		if ent then gii.emitPythonSignal( 'entity.modified', ent ) end	
	end
end

function CmdSetBypassed:undo()
	self.target.FLAG_BYPASSED = self.value0 or nil
	if self.target:isInstance( mock.Entity ) then
		gii.emitPythonSignal( 'entity.modified', self.target )
	else
		local ent = self.target._entity
		if ent then gii.emitPythonSignal( 'entity.modified', ent ) end	
	end
end

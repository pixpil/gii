module 'mock_edit'

--------------------------------------------------------------------
CLASS: DeployTarget ()
	:MODEL{		
		Field "name"      :string() :no_edit();
		Field "lastBuild" :int()    :no_edit(); --timestamp
		Field "state"     :string() :no_edit();		
	}
function DeployTarget:__init()
	self.name = 'TARGET'
end

function DeployTarget:getIcon()
	return nil
end

function DeployTarget:getType()
	return "target"
end

--------------------------------------------------------------------
local deployTargetTypeRegistry = {}

function registerDeployTargetType( name, targetClass )
	deployTargetTypeRegistry[ name ] = targetClass
end

function getDeployTargetTypeRegistry()
	return deployTargetTypeRegistry
end

--------------------------------------------------------------------
CLASS: DeploySceneEntry ()
	:MODEL{
		Field 'path'  :string();
		Field 'alias' :string();
		Field 'entry' :boolean();
		Field 'id'    :int();
	}

function DeploySceneEntry:__init( path )
	self.path  = path
	self.alias = 'Scene'
	self.entry = false
	self.id    = 1
end

---------------------------------------------------------------------
CLASS: DeployManagerConfig ()
	:MODEL{
		Field 'scenes'  :array( DeploySceneEntry );
		Field 'targets' :array( DeployTarget );
	}

function DeployManagerConfig:__init()
	self.scenes  = {}
	self.targets = {}
end

function DeployManagerConfig:addDeployTarget( typeName )
	local clas = deployTargetTypeRegistry[ typeName ]
	assert( clas )
	local target = clas()
	table.insert( self.targets, target )
	return target
end

function DeployManagerConfig:removeDeployTarget( target )
	for i,t in ipairs( self.targets ) do
		if t == target then
			table.remove( self.targets, i )
			break
		end
	end
end

function DeployManagerConfig:addDeployScene( path )
	local entry = DeploySceneEntry( path )
	if not self.scenes[1] then entry.entry = true end
	table.insert( self.scenes, entry )
	self:updateSceneId()
	return entry
end

function DeployManagerConfig:changeTargetScene( entry, scene )
	entry.path = scene
	-- self:updateSceneId()
	return entry
end

function DeployManagerConfig:removeDeployScene( entry )
	for i,t in ipairs( self.scenes ) do
		if t == entry then
			table.remove( self.scenes, i )
			if entry.entry then
				local newEntry = self.scenes[1]
				if newEntry then newEntry.entry = true end
			end
			break
		end
	end
	self:updateSceneId()
end

function DeployManagerConfig:setEntryScene( entry )
	if entry.entry then return end
	entry.entry = true
	for i, t in ipairs( self.scenes ) do
		if t.entry and t ~= entry then t.entry = false end
	end
end 

function DeployManagerConfig:clear()
	self.scenes  = {}
	self.targets = {}
end

function DeployManagerConfig:getTargets()
	return self.targets
end

function DeployManagerConfig:getScenes()
	return self.scenes
end

function DeployManagerConfig:updateSceneId()
	for i, entry in ipairs( self.scenes ) do
		entry.id = i
	end
end

function DeployManagerConfig:moveSceneUp( target )
	for i, entry in ipairs( self.scenes ) do
		if entry == target then
			if i > 1 then
				table.remove( self.scenes, i )
				table.insert( self.scenes, i - 1, target )
			end
			return self:updateSceneId()
		end
	end
end

function DeployManagerConfig:moveSceneDown( target )
	for i, entry in ipairs( self.scenes ) do
		if entry == target then
			if i < #self.scenes then
				table.remove( self.scenes, i )
				table.insert( self.scenes, i + 1, target )
			end
			return self:updateSceneId()
		end
	end
end

function DeployManagerConfig:updateGameConfig()
	local export = {}
	local entryScene
	for i, scn in ipairs( self.scenes ) do
		local alias = scn.alias
		if scn.entry then entryScene = scn.path end
		export[ alias ] = scn.path
	end
	game.scenes = export
	game.entryScene = entryScene
end

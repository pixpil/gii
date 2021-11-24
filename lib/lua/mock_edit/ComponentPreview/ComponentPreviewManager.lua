module 'mock_edit'


--------------------------------------------------------------------
CLASS: ComponentPreviewSession ()
	:MODEL{}

function ComponentPreviewSession:__init()
	self.targetEntity = false
	self.previewers= {}
end

function ComponentPreviewSession:addPreviewerFor( obj )
	if obj.onBuildPreviewer then
		local previewer = obj:onBuildPreviewer()
		if previewer then
			local succ = previewer:onStart()
			if succ == false then
				previewer:onDestroy()
				return false
			end
			self.previewers[ previewer ] = true
			return previewer
		end
	end
	return false
end

function ComponentPreviewSession:init( entity )
	self.targetEntity = entity
	local previewers = self.previewers
	local hasPreviewer = false
	if self:addPreviewerFor( entity ) then hasPreviewer= true end
	if not entity.components then return false end
	for com in pairs( entity.components ) do
		if self:addPreviewerFor( com ) then hasPreviewer= true end
	end
	return hasPreviewer
end

function ComponentPreviewSession:update( dt )
	for previewer in pairs( self.previewers ) do
		previewer:onUpdate( dt )
	end
end

function ComponentPreviewSession:destroy()
	for previewer in pairs( self.previewers ) do
		previewer:onDestroy()
	end
	self.previewers = {}
	self.targetEntity = false
end

function ComponentPreviewSession:reset()
	for previewer in pairs( self.previewers ) do
		previewer:onReset()
	end
end

--------------------------------------------------------------------
CLASS: ComponentPreviewManager ()
	:MODEL{}


function ComponentPreviewManager:__init()
	self.sessions = {}
	self.previewerSettings = {}
	self.autostop = true
	self.enabled  = true
	self.previewChildren = true
end

function ComponentPreviewManager:setOptions( options )
	self.enabled  = options[ 'enabled' ]
	self.autostop = options[ 'autostop' ]
	self.previewChildren = options[ 'previewChildren' ]
end

local function _collectEntityInGroup( group, output )
	if not group:isVisible() then return end
	for e in pairs( group.entities ) do
		if e:isVisible() then 
			output[ e ] = true
		end
	end
	for g in pairs( group.childGroups ) do
		_collectEntityInGroup( g, output )
	end
	return output
end

local function _collectChildren( e, output )
	if not e:isVisible() then return end
	if output[ e ] then return end
	if isInstance( e, mock.Entity ) then
		output[ e ] = true
	end
	for child in pairs( e.children ) do
		_collectChildren( child, output )
	end
	return output
end

function ComponentPreviewManager:buildForMainSceneView()
	if not self.enabled then return end
	local selection = gii.getSelection( 'scene' )
	local sessions = self.sessions
	local previewChildren = self.previewChildren
	--find a parent animator
	local selectedEntities = {}
	for i, ent in ipairs( selection ) do
		if isInstance( ent, mock.Entity ) then	
			if ent:isVisible() then 
				selectedEntities[ ent ] = true
			end
		elseif previewChildren and isInstance( ent, mock.EntityGroup ) then	
			if ent:isVisible() then 
				_collectEntityInGroup( ent, selectedEntities )
			end
		end
	end

	if self.previewChildren then
		local selected2 = {}
		for e in pairs( selectedEntities ) do
			_collectChildren( e, selected2 )
		end
		selectedEntities = selected2
	end

	if self.autostop then
		local stopping = {}
		for ent in pairs( sessions ) do
			if not selectedEntities[ ent ] then --keep
				stopping[ ent ] = true
			end
		end
		for ent in pairs( stopping ) do
			local session = sessions[ ent ]
			session:destroy()
			sessions[ ent ] = nil
		end
	end

	for ent in pairs( selectedEntities ) do
		self:buildForEntity( ent )
	end

end

function ComponentPreviewManager:hasSession()
	return next( self.sessions ) and true or false
end

function ComponentPreviewManager:buildForEntity( ent )
	if self.sessions[ ent ] then return end
	local session = ComponentPreviewSession()
	if session:init( ent, self.previewerSettings ) then
		self.sessions[ ent ] = session
	end
	return session
end

function ComponentPreviewManager:removeForEntity( ent )
	local session = self.sessions[ ent ]
	if not session then return end
	session:destroy()
	self.sessions[ ent ] = nil
end

function ComponentPreviewManager:updateSessions( dt )
	dt = dt or 1/60
	for ent, session in pairs( self.sessions ) do
		session:update( dt )
	end
end

function ComponentPreviewManager:clearSessions()
	for ent, session in pairs( self.sessions ) do
		session:destroy()
	end
	self.sessions = {}
end

function ComponentPreviewManager:resetSessions()
	for ent, session in pairs( self.sessions ) do
		session:reset()
	end
end

--------------------------------------------------------------------
local _ComponentPreviewManager = ComponentPreviewManager()
function getComponentPreviewManager()
	return _ComponentPreviewManager
end

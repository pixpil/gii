module 'mock_edit'


--------------------------------------------------------------------
CLASS: Gizmo ( EditorEntity )
	:MODEL{}

function Gizmo:__init()
	self.items = {}
	self.target = false
	self.targetType = false
	self.selectState = 'unset'
end

function Gizmo:getManager()
	local p = self.parent
	while true do
		if not p then return nil end
		if p:isInstance( GizmoManager ) then return p end
		p = p.parent
	end
end

function Gizmo:enableConstantSize()
	self:getManager():addConstantSizeGizmo( self )
end

function Gizmo:setTarget( object )
	self.target = object
	if isInstance( object, mock.Entity ) then
		self.targetType = 'entity'
	elseif object._entity then
		self.targetType = 'com'
	else
		self.targetType = false
	end
	return self:onInit( object )
end

function Gizmo:onInit( target )
end

function Gizmo:updateCanvas()
	self:getManager():updateCanvas()
end

function Gizmo:onDestroy()
	self:getManager().constantSizeGizmos[ self ] = nil
end

function Gizmo:addCanvasItem( item )
	local view = self:getCurrentView()
	view:addCanvasItem( item )
	self.items[ item ] = true
	return item
end

function Gizmo:removeCanvasItem( item )
	if item then
		item:destroyWithChildrenNow()
	end
end

function Gizmo:onDestroy()
	for item in pairs( self.items ) do
		item:destroyWithChildrenNow()
	end
end

function Gizmo:isPickable()
	return false
end

function Gizmo:onSelectStateChanged( target, state )
end

function Gizmo:isSelected()
	return self.selectState == 'selected'
end

function Gizmo:isParentSelected()
	return self.selectState == 'parent_selected'
end

function Gizmo:isParentOrSelfSelected()
	local ss = self.selectState
	return ss == 'selected' or ss == 'parent_selected'
end

function Gizmo:_updateSelectState( state )
	if state == self.selectState then return end
	self.selectState = state
	return self:onSelectStateChanged( self.target, state )
end


--------------------------------------------------------------------
CLASS: GizmoGroup ( Gizmo )
	:MODEL{}
function GizmoGroup:setTarget( object )
	for child in pairs( self.children ) do
		child:setTarget( object )
	end
	return GizmoGroup.__super.setTarget( self, object )
end

function GizmoGroup:_attachChildEntity( child )
	inheritVisible( child:getProp(), self:getProp() )
	linkLocalVisible( child:getProp(), self:getProp() )
end

function GizmoGroup:_updateSelectState( state )
	if state == self.selectState then return end
	self.selectState = state
	for child in pairs( self.children ) do
		child:_updateSelectState( state )
	end
	return self:onSelectStateChanged( self.target, state )
end

--------------------------------------------------------------------
CLASS: GizmoVisibilityEntry ()
function GizmoVisibilityEntry:__init()
	self.visible      = true
	self.localVisible = true
	self.parent       = false
	self.children     = {}
end

function GizmoVisibilityEntry:isVisible()
	return self.visible
end

function GizmoVisibilityEntry:isLocalVisible()
	return self.localVisible
end

function GizmoVisibilityEntry:setVisible( vis )
	self.localVisible = vis
	self:updateGlobalVisibility()
end

function GizmoVisibilityEntry:toggle()
	self:setVisible( not self.localVisible )
end

function GizmoVisibilityEntry:addChild( child )
	table.insert( self.children, child )
	child.parent = self
	return child
end

function GizmoVisibilityEntry:getParent()
	return self.parent
end

function GizmoVisibilityEntry:updateGlobalVisibility()
	if not self.parent then
		self.visible = self.localVisible
	else
		self.visible = self.parent.visible and self.localVisible
	end
	for i, child in ipairs( self.children ) do
		child:updateGlobalVisibility()
	end
end

function GizmoVisibilityEntry:reset()
	self.localVisible = true
	for i, child in ipairs( self.children ) do
		child:reset()
	end
end

function GizmoVisibilityEntry:isGroup()
	return false
end

function GizmoVisibilityEntry:getLabel()
	return self.name
end

function GizmoVisibilityEntry:save( data )
end

--------------------------------------------------------------------
CLASS: GizmoVisibilityGroup ( GizmoVisibilityEntry )
function GizmoVisibilityGroup:__init()
	self.category = false
	self.fullCategory = false
end

function GizmoVisibilityGroup:isGroup()
	return true
end

function GizmoVisibilityGroup:getLabel()
	return '<'..self.category..'>'
end

function GizmoVisibilityGroup:save( data )
	data.groups[ self.fullCategory ] = self.localVisible
	for i, child in ipairs( self.children ) do
		child:save( data )
	end
end

function GizmoVisibilityGroup:load( data )
	self.localVisible = data.groups[ self.fullCategory ]
	for i, child in ipairs( self.children ) do
		child:load( data )
	end
end

--------------------------------------------------------------------
CLASS: GizmoVisibilityItem ( GizmoVisibilityEntry )
function GizmoVisibilityItem:__init()
	self.targetClass = false
end

function GizmoVisibilityItem:getLabel()
	return self.targetClass:getClassName()
end

function GizmoVisibilityItem:save( data )
	if not self.targetClass then return end
	local fullname = self.targetClass:getClassFullName()
	data.items[ fullname ] = self.localVisible
end

function GizmoVisibilityItem:load( data )
	if not self.targetClass then return end
	local fullname = self.targetClass:getClassFullName()
	self.localVisible = data.items[ fullname ] ~= false
end

CLASS: GizmoVisibilityRoot ( GizmoVisibilityGroup )

function GizmoVisibilityRoot:__init()
	self.category = '__root__'
	self.fullCategory = '__root__'
end

function GizmoVisibilityRoot:getLabel()
	return 'ALL'
end


--------------------------------------------------------------------
CLASS: GizmoManager ( SceneEventListener )
	:MODEL{}

function GizmoManager:__init()
	self.normalGizmoMap   = {}
	self.selectedGizmoMap = {}
	self.constantSizeGizmos = {}
	self.gizmoVisible = true
	self.clasToVisEntry    = {}
	self:buildVisibilityTree()
end

function GizmoManager:onLoad()
	local view = self.parent
	local cameraListenerNode = MOAIScriptNode.new()
	local cameraCom = view:getCameraComponent()
	cameraListenerNode:setNodeLink( cameraCom.zoomControlNode )
	if cameraCom:isPerspective() then
		cameraListenerNode:setNodeLink( cameraCom:getMoaiCamera() )
	end
	self.cameraListenerNode = cameraListenerNode
	self:scanScene()
end

function GizmoManager:onDestroy()
end

function GizmoManager:buildVisibilityTree()
	local componentCategories = mock.buildComponentCategories()
	local entityCategories    = mock.buildEntityCategories()
	local root = GizmoVisibilityRoot()
	clasToVisEntry = {}
	local merged = {}
	for k, category in pairs( componentCategories ) do
		merged[ k ] = table.simplecopy( category )
	end
	for k, category in pairs( entityCategories ) do
		local g0 = merged[ k ]
		local classEntries = {}
		for i, entry in ipairs( category ) do
			if isClass( entry[2] ) then
				table.insert( classEntries, entry )
			end
		end
		if not g0 then
			merged[ k ] = table.simplecopy( classEntries )
		else
			merged[ k ] = table.join( g0, classEntries )
		end
	end

	for k, category in pairs( merged ) do
		local group = GizmoVisibilityGroup()
		group.category = k
		group.fullCategory = k
		root:addChild( group )
		if k == '__unsorted__' then
			group.category = 'Unsorted'
		end
		for i, entry in ipairs( category ) do
			local name, clas, cat = unpack( entry )
			if clas.onBuildGizmo or clas.onBuildSelectedGizmo then
				local visItem = GizmoVisibilityItem()
				visItem.targetClass = clas
				group:addChild( visItem )
				clasToVisEntry[ clas ] = visItem
			end
		end
	end
	self.visiblityTreeRoot = root
	self.clasToVisEntry = clasToVisEntry
end

function GizmoManager:getVisiblityTreeRoot()
	return self.visiblityTreeRoot
end

function GizmoManager:toggleVisibility( visEntry )
	visEntry:toggle()
	self:updateGizmoVisibility()
end

function GizmoManager:isObjectGizmoVisible( obj )
	local visEntry = self:getVisEntry( obj )
	if not visEntry then return true end
	return visEntry:isVisible()
end

function GizmoManager:getVisEntry( obj )
	local clas = getClass( obj )
	local entry = self.clasToVisEntry[ clas ]
	if entry ~= nil then return entry end
	local super = clas.__super
	while super do
		entry = self.clasToVisEntry[ super ]
		if entry then
			self.clasToVisEntry[ clas ] = entry
			return entry
		end
		super = super.__super
	end
	self.clasToVisEntry[ clas ] = false
	return false
end

function GizmoManager:updateGizmoVisibility()
	for obj, giz in pairs( self.normalGizmoMap ) do
		giz:setVisible( self:isObjectGizmoVisible( obj ) )
	end
	for obj, giz in pairs( self.selectedGizmoMap ) do
		giz:setVisible( self:isObjectGizmoVisible( obj ) )
	end
end

function GizmoManager:resetGizmoVisibility()
	self:getVisiblityTreeRoot():reset()
	self:getVisiblityTreeRoot():updateGlobalVisibility()
	self:updateGizmoVisibility()
end

function GizmoManager:saveVisibility()
	local data = self.visiblityData 
	if not data then
		data = {
			groups = {},
			items  = {}
		}
		self.visiblityData = data
	end
	self:getVisiblityTreeRoot():save( data )
	return data
end

function GizmoManager:loadVisibility( data )
	if not data then return end
	self.visiblityData = data
	self:getVisiblityTreeRoot():load( data )
	self:getVisiblityTreeRoot():updateGlobalVisibility()
	self:updateGizmoVisibility()
end


function GizmoManager:updateConstantSizeForGizmo( giz )
	local view = self.parent
	local cameraCom = view:getCameraComponent()
	local factorZoom = 1/cameraCom:getZoom()
	local factorDistance = 1
	if cameraCom:isPerspective() then
		--TODO
	end
	local scl = factorZoom * factorDistance
	giz:setScl( scl, scl, scl )
	giz:forceUpdate()
end

function GizmoManager:preCanvasDraw()
	self:updateConstantSize()
end

function GizmoManager:updateConstantSize()
	for giz in pairs( self.constantSizeGizmos ) do
		self:updateConstantSizeForGizmo( giz )
	end
end

function GizmoManager:_attachChildEntity( child )
	-- linkLocalVisible( self:getProp(), child:getProp() )
end

local function _getEntitySelectState( ent, set )
	if set[ ent ] then return 'selected' end
	local p = ent.parent
	while p do
		if set[ p ] then return 'parent_selected' end
		p = p.parent
	end
	return false
end

function GizmoManager:onSelectionChanged( selection )
	--clear selection gizmos
	for ent, giz in pairs( self.selectedGizmoMap ) do
		giz:destroyWithChildrenNow()
	end
	self.selectedGizmoMap = {}
	local entitySet = {}
	for i, e in ipairs( selection ) do
		entitySet[ e ] = true
	end

	--update selected state
	for target, giz in pairs( self.normalGizmoMap ) do
		local gt = giz.targetType
		local sstate
		if gt == 'entity' then
			sstate = _getEntitySelectState( target, entitySet )
		elseif gt == 'com' then
			sstate = _getEntitySelectState( target._entity, entitySet )
		end
		if sstate ~= nil then
			giz:_updateSelectState( sstate )
		end
	end

	local topEntitySet = findTopLevelEntities( entitySet )
	for e in pairs( topEntitySet ) do
		if isInstance( e, mock.Entity ) then
			self:buildForEntity( e, true )
		end
	end
	
	-- self:updateCanvas()
end

function GizmoManager:onEntityEvent( ev, entity, com )
	if ev == 'clear' then
		self:clear()
		return
	end

	if entity.FLAG_EDITOR_OBJECT then return end

	if ev == 'add' then
		self:buildForEntity( entity ) 
	elseif ev == 'remove' then
		self:removeForEntity( entity )
	elseif ev == 'attach' then
		self:buildForObject( com )
	elseif ev == 'detach' then
		self:removeForObject( com )
	end

end

function GizmoManager:addConstantSizeGizmo( giz )
	self.constantSizeGizmos[ giz ] = true	
	self:updateConstantSizeForGizmo( giz )
end

function GizmoManager:refresh()
	self:clear()
	self:scanScene()
	self:updateConstantSize()
end

function GizmoManager:scanScene()
	local entities = table.simplecopy( self.scene.entities )
	for e in pairs( entities ) do
		self:buildForEntity( e, false )
	end
end

function GizmoManager:buildForEntity( ent, selected )
	if ent.components then
		if not ( ent.FLAG_INTERNAL or ent.FLAG_EDITOR_OBJECT or ent:isEditLocked() ) then
			self:buildForObject( ent, selected )
			for c in pairs( ent.components ) do
				if not ( c.FLAG_EDITOR_OBJECT ) then
					self:buildForObject( c, selected )
				end
			end
			for child in pairs( ent.children ) do
				self:buildForEntity( child, selected )
			end
		end
	end
end

function GizmoManager:buildForObject( obj, selected )
	if obj.FLAG_INTERNAL then return end
	local onBuildGizmo
	if selected then 
		onBuildGizmo = obj.onBuildSelectedGizmo
	else
		onBuildGizmo = obj.onBuildGizmo
	end

	if onBuildGizmo then
		local gizmos = { onBuildGizmo( obj ) }
		local giz
		if #gizmos > 1 then
			giz = GizmoGroup()
			for i, subGiz in ipairs( gizmos ) do
				giz:addChild( subGiz )
			end
		else
			giz = gizmos[ 1 ]
		end

		if giz then
			if not isInstance( giz, Gizmo ) then
				_warn( 'Invalid gizmo type given by', obj:getClassName() )
				return
			end

			if selected then
				local giz0 = self.selectedGizmoMap[ obj ]
				if giz0 then giz0:destroyWithChildrenNow() end
				self.selectedGizmoMap[ obj ] = giz
				giz:setVisible( self:isObjectGizmoVisible( obj ) )
				giz:_updateSelectState( 'selected' )
			else
				local giz0 = self.normalGizmoMap[ obj ]
				if giz0 then giz0:destroyWithChildrenNow() end
				self.normalGizmoMap[ obj ] = giz
				giz:setVisible( self:isObjectGizmoVisible( obj ) )
				giz:_updateSelectState( false )
			end

			self:addChild( giz )
			if obj:isInstance( mock.Entity ) then
				inheritVisible( giz:getProp(), obj:getProp() )
			elseif obj._entity then
				inheritVisible( giz:getProp(), obj._entity:getProp() )
			end
			giz:setTarget( obj )
		end

	end

end

function GizmoManager:setGizmoVisible( vis )
	self.gizmoVisible = vis
	-- for _, giz in pairs( self.normalGizmoMap ) do
	-- 	giz:setVisible( vis )
	-- end
end


function GizmoManager:isGizmoVisible()
	return self.gizmoVisible
end


function GizmoManager:removeForObject( obj )
	local giz = self.normalGizmoMap[ obj ]
	if giz then
		giz:destroyWithChildrenNow()
		self.normalGizmoMap[ obj ] = nil
	end
end

function GizmoManager:removeForEntity( ent )
	for com in pairs( ent.components ) do
		self:removeForObject( com )
	end
	for child in pairs( ent.children ) do
		self:removeForEntity( child )
	end
	self:removeForObject( ent )
end

function GizmoManager:clear()
	self:clearChildrenNow()
	self.normalGizmoMap   = {}
	self.selectedGizmoMap = {}
end


function GizmoManager:pickPoint( x,y )
	--TODO
end

function GizmoManager:pickRect( x,y, x1, y1  )
	--TODO
end


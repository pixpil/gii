module 'mock_edit'

local function collectRenderComponent( e, collection )
	if isEditorEntity( e ) then return end
	if not isInstance( e, mock.Entity ) then return end
	for child in pairs( e.children ) do
		collectRenderComponent( child, collection )
	end
	local result = {}
	for com in pairs( e.components ) do
		if isInstance( com, mock.RenderComponent ) then
			collection[ com ] = true
		end
	end
end

--------------------------------------------------------------------
CLASS: CmdFillRenderMaterial ( mock_edit.EditorCommand )
	:register( 'scene_editor/fill_render_material' )

function CmdFillRenderMaterial:init( option )
	-- print( 'toggle floor helper:', option.toggle )
	local sceneView = mock_edit.getCurrentSceneView()
	if not sceneView then return end

	local selection = gii.getSelection( 'scene' )
	local collection = {}
	for i, e in pairs( selection ) do
		collectRenderComponent( e, collection )
	end

	local overwrite = option['overwrite'] or false

	local assetSelection = gii.getSelection( 'asset' )
	local targetMaterial = false
	for i, node in ipairs( assetSelection ) do
		local atype = node:getType()
		if atype == 'material' then
			targetMaterial = node:getNodePath()
		end
	end

	if not targetMaterial then
		mock_edit.alertMessage( 'message', 'no render material is selected', 'info' )
		return false
	end

	local targets = {}
	for com in pairs( collection ) do
		local material = com:getMaterial()
		if not material then
			targets[ com ] = false
		elseif overwrite then
			targets[ com ] = material
		end
	end

	self.targetMaterial = targetMaterial
	self.targetComponents = targets

end

function CmdFillRenderMaterial:redo()
	local targets = self.targetComponents
	for com in pairs( targets ) do
		com:setMaterial( self.targetMaterial )
	end
	gii.emitPythonSignal( 'scene.update' )
end

function CmdFillRenderMaterial:undo()
	local targets = self.targetComponents
	for com, prev in pairs( targets ) do
		com:setMaterial( prev )
	end
	gii.emitPythonSignal( 'scene.update' )
end


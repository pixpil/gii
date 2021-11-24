module 'mock_edit'

local function findTopNodes( nodeSet )
	local found = {}
	for node in pairs( nodeSet ) do
		local p = node.parent
		local isTop = true
		while p do
			if nodeSet[ p ] then isTop = false break end
			p = p.parent
		end
		if isTop then found[node] = true end
	end
	return found
end

--------------------------------------------------------------------
CLASS: CmdAnimatorCloneKey( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_clone_key' )



--------------------------------------------------------------------
CLASS: CmdAnimatorReparentTrack ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_reparent_track' )


function CmdAnimatorReparentTrack:init( option )
	local sources = gii.listToTable( option['source'] )
	local sourceSet = {}
	for i, node in ipairs( sources ) do
		sourceSet[ node ] = true
	end
	sourceSet = findTopNodes( sourceSet )
	local target = option['target']
	if target == 'root' then
		local node1 = next( sourceSet )
		target = node1:getRoot()
	end
	
	--validate
	local valid = true
	for node in pairs( sourceSet ) do
		if not node:canReparent( target ) then
			valid = false
			_warn( 'cannot reparent track', node:toString(), '->', target:toString() )
		end
	end
	if not valid then
		return false
	end

	local prevParents = {}
	for node in pairs( sourceSet ) do
		prevParents[ node ] = node.parent
	end
	self.prevParents = prevParents
	self.source = sourceSet
	self.target = target
end

function CmdAnimatorReparentTrack:redo()
	local target = self.target
	for node in pairs( self.source ) do
		node:reparent( target )
	end
	local view = gii.getModule( 'animator_view' )
	if view then
		view:refreshTimeline()
	end
end

function CmdAnimatorReparentTrack:undo()
	local prevParents = self.prevParents
	for node in pairs( self.source ) do
		local prevParent = prevParents[ node ]
		node:reparent( prevParent )
	end
end


--------------------------------------------------------------------
CLASS: CmdAnimatorAddClipTree ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_add_clip_tree' )
function CmdAnimatorAddClipTree:init( option )
	self.targetAnimatorData = option[ 'animator_data' ]
	self.targetParentGroup  = option[ 'parent_group'  ]
	self.createdClipTree = false
end

function CmdAnimatorAddClipTree:redo()
	if not self.createdClipTree then
		self.createdClipTree = self.targetAnimatorData:createClipTree(
			'New Clip Tree',
			self.targetParentGroup
		)
	else
		self.targetAnimatorData:addClip( self.createdClipTree, self.targetParentGroup )
	end
end

function CmdAnimatorAddClipTree:undo()
	self.targetAnimatorData:removeClip( self.createdClipTree )
end

function CmdAnimatorAddClipTree:getResult()
	return self.createdClipTree
end

--------------------------------------------------------------------
CLASS: CmdAnimatorAddClip ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_add_clip' )
function CmdAnimatorAddClip:init( option )
	self.targetAnimatorData = option[ 'animator_data' ]
	self.targetParentGroup  = option[ 'parent_group'  ]
	self.createdClip = false
end

function CmdAnimatorAddClip:redo()
	if not self.createdClip then
		self.createdClip = self.targetAnimatorData:createClip(
			'New Clip',
			self.targetParentGroup
		)
	else
		self.targetAnimatorData:addClip( self.createdClip, self.targetParentGroup )
	end
end

function CmdAnimatorAddClip:undo()
	self.targetAnimatorData:removeClip( self.createdClip )
end

function CmdAnimatorAddClip:getResult()
	return self.createdClip
end

--------------------------------------------------------------------
CLASS: CmdAnimatorAddClipGroup ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_add_clip_group' )

function CmdAnimatorAddClipGroup:init( option )
	self.targetAnimatorData = option[ 'animator_data' ]
	self.targetParentGroup  = option[ 'parent_group'  ]
	self.createdGroup = false
end

function CmdAnimatorAddClipGroup:redo()
	if not self.createdGroup then
		self.createdGroup = self.targetAnimatorData:createClipGroup(
			'New Group',
			self.targetParentGroup
		)
	else
		self.targetAnimatorData:addClip( self.createdGroup, self.targetParentGroup )
	end
end

function CmdAnimatorAddClipGroup:undo()
	self.targetAnimatorData:removeClip( self.createdGroup )
end

function CmdAnimatorAddClipGroup:getResult()
	return self.createdGroup
end

--------------------------------------------------------------------
CLASS: CmdAnimatorRemoveClipNode ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_remove_clip_node' )

function CmdAnimatorRemoveClipNode:init( option )
	self.targetAnimatorData = option[ 'animator_data' ]
	self.targetNode         = option[ 'target_node'  ]
	self.targetParentGroup  = self.targetNode.parentGroup
end

function CmdAnimatorRemoveClipNode:redo()
	if self.targetNode:isInstance( mock.AnimatorClip ) then
		self.targetParentGroup:removeChildClip( self.targetNode )
	else
		self.targetParentGroup:removeChildGroup( self.targetNode )
	end
end

function CmdAnimatorRemoveClipNode:undo()
	if self.targetNode:isInstance( mock.AnimatorClip ) then
		self.targetParentGroup:addChildClip( self.targetNode )
	else
		self.targetParentGroup:addChildGroup( self.targetNode )
	end
end


--------------------------------------------------------------------
CLASS: CmdAnimatorCloneClipNode ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_clone_clip_node' )

function CmdAnimatorCloneClipNode:init( option )
	self.targetAnimatorData = option[ 'animator_data' ]
	self.targetNode         = option[ 'target_node'  ]
	self.targetParentGroup  = self.targetNode.parentGroup
	self.cloned = false
end

function CmdAnimatorCloneClipNode:redo()
	if not self.cloned then
		local serializedData = mock.serialize( self.targetNode )
		local cloned = mock.deserialize( nil, serializedData )
		cloned.name = cloned.name .. '_copy'
		cloned.parentGroup = false
		self.cloned = cloned
	end

	local cloned = self.cloned
	cloned:_postLoad()
	if cloned:isInstance( mock.AnimatorClip ) then
		self.targetAnimatorData:addClip( cloned, self.targetParentGroup )
	else
		self.targetAnimatorData:addClipGroup( cloned, self.targetParentGroup )
	end
end

function CmdAnimatorCloneClipNode:undo()
	local cloned = self.cloned
	if cloned:isInstance( mock.AnimatorClip ) then
		self.targetAnimatorData:removeClip( cloned )
	else
		self.targetAnimatorData:removeClipGroup( cloned )
	end
end

function CmdAnimatorCloneClipNode:getResult()
	return self.cloned
end


--------------------------------------------------------------------
CLASS: CmdAnimatorReparentClip ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_reparent_clip' )


function CmdAnimatorReparentClip:init( option )
	local sources = gii.listToTable( option['source'] )
	local sourceSet = {}
	for i, node in ipairs( sources ) do
		sourceSet[ node ] = true
	end

	local target = option['target']
	if target == 'root' then
		local node1 = next( sourceSet )
		target = node1:getRootGroup()
	end
	
	if not target:isInstance( mock.AnimatorClipGroup ) then
		target = target:getParentGroup()
	end
	
	local prevParents = {}
	for node in pairs( sourceSet ) do
		prevParents[ node ] = node:getParentGroup()
	end
	self.prevParents = prevParents
	self.source = sourceSet
	self.target = target
end

function CmdAnimatorReparentClip:redo()
	local target = self.target
	for node in pairs( self.source ) do
		node:setParentGroup( target )
	end
	local view = gii.getModule( 'animator_view' )
	if view then
		view:refreshClipList()
	end
end

function CmdAnimatorReparentClip:undo()
	local prevParents = self.prevParents
	for node in pairs( self.source ) do
		local prevParent = prevParents[ node ]
		node:setParentGroup( prevParent )
	end
	local view = gii.getModule( 'animator_view' )
	if view then
		view:refreshClipList()
	end
end


---------------------------------------------------------------------
CLASS: CmdAnimatorAddTrack ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_add_track' )

--------------------------------------------------------------------
CLASS: CmdAnimatorAddMarker ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_add_marker')

function CmdAnimatorAddMarker:init( option )
	self.targetClip     = option[ 'target_clip'  ]
	self.targetPos      = option[ 'target_pos' ] or 0
	self.createdMarker  = false
end

function CmdAnimatorAddMarker:redo()
	local marker = self.targetClip:addMarker()
	if self.createdMarker then --TODO
		_cloneObject( self.createdMarker, marker )
	else
		marker:setPos( self.targetPos )
	end
	self.createdMarker = marker
end

function CmdAnimatorAddMarker:undo()
	self.targetClip:removeMarker( self.createdMarker )
end

function CmdAnimatorAddMarker:getResult()
	return self.createdMarker
end


--------------------------------------------------------------------
CLASS: CmdAnimatorAddClipTreeNode ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_add_clip_tree_node')

function CmdAnimatorAddClipTreeNode:init( option )
	self.parentTree  = option['parent_tree']
	self.nodeType    = option['node_type']
	self.contextNode =  option['context_node'] or self.parentTree:getTreeRoot()
	self.createdNode  = false
	--TODO: validate availbility
	if not self.contextNode:acceptChildType( self.nodeType ) then
		mock_edit.alertMessage( 'Warn', 'Invalid child node type', 'info' )
		return false
	end
end

function CmdAnimatorAddClipTreeNode:redo()
	if self.createdNode then --TODO
		self.contextNode:addChild( self.createdNode )
	else
		local clas = mock.getAnimatorClipTreeNodeType( self.nodeType )
		local node = clas()
		node:initFromEditor()
		self.contextNode:addChild( node )
		self.createdNode = node
	end
end

function CmdAnimatorAddClipTreeNode:undo()
	self.contextNode:removeChild( self.createdNode )
end

function CmdAnimatorAddClipTreeNode:getResult()
	return self.createdNode
end


--------------------------------------------------------------------
CLASS: CmdAnimatorRemoveClipTreeNode ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_remove_clip_tree_node' )

function CmdAnimatorRemoveClipTreeNode:init( option )
	self.targetNode         = option[ 'target_node'  ]
	self.targetParentNode  = self.targetNode.parent
end

function CmdAnimatorRemoveClipTreeNode:redo()
	self.targetParentNode:removeChild( self.targetNode )
end

function CmdAnimatorRemoveClipTreeNode:undo()
	self.targetParentNode:addChild( self.targetNode )
end



--------------------------------------------------------------------
function requestAvailAnimatorClipTreeNodeTypes( parentNode )
	local reg = mock.getAnimatorClipTreeNodeTypeRegistry()
	local result = {}
	for name, clas in pairs( reg ) do
		if parentNode:acceptChildType( name ) then
			table.insert( result, name )
		end
	end
	return result
end

-- function createAnimatorClipTreeNode( name, contextNode, contextRoutine )
-- 	local entry = mock.findInSQNodeRegistry( name )
-- 	if not entry then
-- 		_warn( 'sq node registry not found', name )
-- 		return nil
-- 	end
-- 	local clas = entry.clas
-- 	local node = clas()
-- 	node:initFromEditor()
-- 	if not contextNode then --root node
-- 		contextRoutine:addNode( node )
-- 	else
-- 		if contextNode:isGroup() and contextNode:canInsert() then
-- 			contextNode:addChild( node )
-- 		else
-- 			local parentNode = contextNode:getParent()
-- 			local index = parentNode:indexOfChild( contextNode )
-- 			parentNode:addChild( node, index+1 )
-- 		end
-- 	end
-- 	return node
-- end



--------------------------------------------------------------------
CLASS: CmdAnimatorRetargetTrack ( mock_edit.EditorCommand )
	:register( 'scene_editor/animator_retarget_track' )

function CmdAnimatorRetargetTrack:init( option )
	self.targetTrack         = option[ 'target_track' ]
	self.targetEntity        = option[ 'target_entity' ]
	self.animator            = option[ 'animator' ]
end

function CmdAnimatorRetargetTrack:redo()
	--TODO: match component / validation
	local rootEntity = self.animator and self.animator._entity
	local originalPath = self.targetTrack.targetPath
	local newPath
	if originalPath:isEntityTarget() then
		newPath = mock.AnimatorTargetPath.buildFor( self.targetEntity, rootEntity )

	else
		local originalClass = originalPath:getTargetClass()
		local targetCom = self.targetEntity:com( originalClass )
		if targetCom then
			newPath = mock.AnimatorTargetPath.buildFor( targetCom, rootEntity )
		else
			_warn( 'no component in target', originalClass )
		end
		
	end
	self.targetTrack:setTargetPath( newPath )
	-- self.targetParentNode:removeChild( self.targetNode )
end

function CmdAnimatorRetargetTrack:undo()
	--TODO
end


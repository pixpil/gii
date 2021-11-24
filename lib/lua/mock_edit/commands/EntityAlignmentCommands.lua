module 'mock_edit'
--------------------------------------------------------------------
CLASS: CmdAlignEntities ( mock_edit.EditorCommand )
	:MODEL{}

function CmdAlignEntities:init( option )
	local targets = getTopLevelEntitySelection()
	local mode = option['mode']
	self.targets = targets
	if not mode then return false end
	if not next( targets ) then return false end
end

function CmdAlignEntities:redo()
end

function CmdAlignEntities:undo()
	--TODO:undo
end

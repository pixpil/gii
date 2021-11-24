module 'mock_edit'

--------------------------------------------------------------------
--COMMAND: create global object
--------------------------------------------------------------------
CLASS: CmdCreateGlobalObject ( EditorCommand )
	:register( 'scene_editor/create_global_object' )

function CmdCreateGlobalObject:init( option )
	self.className = option.name
end

function CmdCreateGlobalObject:redo()
	local objClas = mock.getGlobalObjectClass( self.className )
	assert( objClas )
	local object = objClas()
	self.created = object
	local lib = mock.game:getGlobalObjectLibrary()
	local node = lib.root:addObject( 'object', object )
	gii.emitPythonSignal('global_object.added', node )
end

function CmdCreateGlobalObject:undo()
	--TODO
	gii.emitPythonSignal('global_object.removed', self.created )
end


--------------------------------------------------------------------
--COMMAND: remove global object
--------------------------------------------------------------------
CLASS: CmdRemoveGlobalObject ( EditorCommand )
	:register( 'scene_editor/remove_global_object' )

function CmdRemoveGlobalObject:init( option )
	self.target = option.target
end

function CmdRemoveGlobalObject:redo()
	--TODO!!!!
	local target = self.target
	local parent = target and target.parent
	if parent then
		parent:removeNode( target.name )
		gii.emitPythonSignal( 'global_object.removed', target )
		return true
	else
		return false
	end
end

function CmdRemoveGlobalObject:undo()
	--TODO
	local target, parent = self.target, self.parent
	parent:addNode( target.name, target )
	gii.emitPythonSignal('global_object.added', target, 'undo' )

end


--------------------------------------------------------------------
--COMMAND: clone global object
--------------------------------------------------------------------
CLASS: CmdCloneGlobalObject ( EditorCommand )
	:register( 'scene_editor/clone_global_object' )

function CmdCloneGlobalObject:init( option )
	self.className = option.name
end

function CmdCloneGlobalObject:redo()
	--TODO!!!!
end

function CmdCloneGlobalObject:undo()
	--TODO
	gii.emitPythonSignal('global_object.removed', self.created )
end



--------------------------------------------------------------------
--COMMAND: reparent global object
--------------------------------------------------------------------
CLASS: CmdReparentGlobalObject ( EditorCommand )
	:register( 'scene_editor/reparent_global_object' )

function CmdReparentGlobalObject:init( option )
	self.target = option.target or 'root'
	self.sources = gii.listToTable( option.sources or {} )
	self.prevParents = {}
	for i, src in ipairs( self.sources ) do
		self.prevParents[ i ] = src.parent
	end
end

function CmdReparentGlobalObject:redo()
	local lib = mock.game:getGlobalObjectLibrary()
	local target = self.target
	if not target or target == 'root' then
		target = lib.root
	end
	for i, src in ipairs( self.sources ) do
		src:reparent( target )
	end
end

function CmdReparentGlobalObject:undo()
	--TODO
	for i, src in ipairs( self.sources ) do
		prevParent = self.prevParents[ i ]
		src:reparent( prevParent )
	end
end



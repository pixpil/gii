require 'mock'

function addObject()
	local lib = mock.game:getGlobalObjectLibrary()
	local node = lib.root:addObject( 'object', Entity() )
	return node
end

function addGroup()
	local lib = mock.game:getGlobalObjectLibrary()
	local node = lib.root:addGroup( 'group' )
	return node
end

function renameObject( node, name )
	node:setName( name )
end

function remove( node )
	node.parent:removeNode( node.name )
end

function reloadObjects()
	local lib = mock.game:getGlobalObjectLibrary()
	lib:reload()
end



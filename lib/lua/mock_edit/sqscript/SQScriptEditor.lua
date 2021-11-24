module 'mock_edit'

function requestAvailSQNodeTypes( parentNode )
	local reg = mock.getSQNodeRegistry()
	local result = {}
	for name, entry in pairs( reg ) do
		if parentNode:acceptSubNode( name ) then
			table.insert( result, name )
		end
	end
	return result
end

function createSQNode( name, contextNode, contextRoutine )
	local entry = mock.findInSQNodeRegistry( name )
	if not entry then
		_warn( 'sq node registry not found', name )
		return nil
	end
	local clas = entry.clas
	local node = clas()
	node:initFromEditor()
	if not contextNode then --root node
		contextRoutine:addNode( node )
	else
		if contextNode:isGroup() and contextNode:canInsert() then
			contextNode:addChild( node )
		else
			local parentNode = contextNode:getParent()
			local index = parentNode:indexOfChild( contextNode )
			parentNode:addChild( node, index+1 )
		end
	end
	return node
end


module 'mock_edit'
function listQuestNodeNames()
	local qm = mock.getQuestManager()
	local result = {}
	for i, session in ipairs( qm.sessions ) do
		local state = session.state
		for i, scheme in ipairs( state.schemes ) do
			for n, node in pairs( scheme.nodeByName ) do
				local name = session.name..':'..node:getFullName()
				table.insert( result, name )
			end
		end
	end
	return result
end

--------------------------------------------------------------------
config = mock_edit.DeployManagerConfig()

function loadDeployManagerConfig( configFile )
	local file = io.open( configFile, 'rb' )
	
	if not file then 
		mock._stat('no deploy config file found')
		return
	end

	file:close()
	config:clear()
	mock.deserializeFromFile( config, configFile )
	updateGameConfig()
end

function saveDeployManagerConfig( configFile )
	mock.serializeToFile( config, configFile )
	updateGameConfig()
end

function updateGameConfig()
	config:updateGameConfig()	
end

function getDeployTargetTypeRegistry()
	return mock_edit.getDeployTargetTypeRegistry()
end

	

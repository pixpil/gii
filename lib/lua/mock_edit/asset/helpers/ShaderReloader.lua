module 'mock_edit'

local function reloadShaderConfig( config )
	if not config then return end
	config:reload()
	config:rebuild()
	
end

local function onAssetModified( node )
	local atype = node:getType()
	local toUpdate = {}

	if atype == 'fsh' or atype == 'vsh' or atype == 'glsl' then
		local path = node:getNodePath()
		local programs = mock.getLoadedShaderPrograms()
		local toUpdate = {}
		for prog in pairs( programs ) do
			if   prog.vshPath == path 
				or prog.fshPath == path
				or prog.tshPath == path
				or prog.gshPath == path
			then
				local parentConfig = prog.parentConfig
				if parentConfig then
					toUpdate[ parentConfig ] = true
				end
			end
		end
		for config in pairs( toUpdate ) do
			reloadShaderConfig( config )
		end

	elseif atype == 'shader' or atype == 'shader_script' then
		local config = node:getCacheData( 'config' )
		if config then
			reloadShaderConfig( config )
		end

	else
		return

	end
	gii.emitPythonSignal( 'scene.update' )

end

connectSignalFunc( 'asset.modified', onAssetModified )


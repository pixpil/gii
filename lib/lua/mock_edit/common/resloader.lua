function loadShader(option)
	local vsh,fsh=option.vsh,option.fsh

	local program=MOAIShaderProgram.new()
	program:load(vsh,fsh)
	if option.name then program.name=option.name end

	--setup variables

	if option.onLoad then option.onLoad(program)	end
	local attrs = option.attributes or {'position', 'uv', 'color'}
	if attrs then
		for i, a in ipairs(attrs) do
			assert(type(a)=='string')
			program:setVertexAttribute(i,a)
		end
	end

	local uniforms=option.uniforms
	local uniformTable = {}
	if uniforms then
		local count=#uniforms
		program:reserveUniforms(count)
		for i, u in ipairs(uniforms) do
			local utype=u.type
			local uvalue=u.value
			local name=u.name

			if utype=='float' then
				program:declareUniformFloat(i, name, uvalue or 0)
			elseif utype=='int' then
				program:declareUniformInt(i, name, uvalue or 0)			
			elseif utype=='color' then
				program:declareUniform(i,name,MOAIShaderProgram.UNIFORM_COLOR)
			elseif utype=='sampler' then
				program:declareUniformSampler(i, name, uvalue or 1)
			elseif utype=='transform' then
				program:declareUniform(i,name, MOAIShaderProgram.UNIFORM_TRANSFORM)
			elseif utype=='pen_color' then
				program:declareUniform(i,name,MOAIShaderProgram.UNIFORM_PEN_COLOR)
			elseif utype=='view_proj' then
				program:declareUniform(i,name,MOAIShaderProgram.UNIFORM_VIEW_PROJ)
			elseif utype=='world_view_proj' then
				program:declareUniform(i,name,MOAIShaderProgram.UNIFORM_WORLD_VIEW_PROJ)
			end
			uniformTable[ name ] = i
		end
	end
	program.uniformTable = uniformTable
	local shader = MOAIShader.new()
	
	shader:setProgram( program )
	local _setAttr = shader.setAttr
	function shader:setAttr( name, v )
		local tt = type( name )
		if tt == 'number' then return _setAttr( self, name, v )  end
		local ut = self.uniformTable
		local id = ut[ name ]
		if not id then error('undefined uniform:'..name, 2) end
		_setAttr( self, id, v )
	end

	local _setAttrLink = shader.setAttrLink
	function shader:setAttrLink( name, v )
		local tt = type( name )
		if tt == 'number' then return _setAttrLink( self, name, v )  end
		local ut = self.uniformTable
		local id = ut[ name ]
		if not id then error('undefined uniform:'..name, 2) end
		_setAttrLink( self, id, v )
	end

	return shader
end

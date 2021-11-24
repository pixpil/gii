local bridge = GII_PYTHON_BRIDGE
local modelBridge = bridge.ModelBridge.get()

module('gii',package.seeall)


--------------------------------------------------------------------
-- MODEL BRIDGE
--------------------------------------------------------------------
local function typeIdGetter(v)	
	local tt = type(v)
	if tt == 'table' then
		local mt = getmetatable(v)
		if not mt then return nil end
		return mt
	elseif tt == 'userdata' then
		local getClass = v.getClass
		if getClass then
			return getClass(v)
		end
	end
	
	return nil
end

local function modelGetter(o)
	return nil
end

local function modelFromType(t)
	return nil
end

registerModelProvider{
	name               = 'MOAIModelProvider',
	priority           = 10,
	getTypeId          = typeIdGetter,
	getModel           = modelGetter,
	getModelFromTypeId = modelFromType
}

-- --------------------------------------------------------------------
-- local function _method(id)
-- 	return function(obj,...) return obj[id](obj, ...) end
-- end
-- local function _moai_get_attr(id)
-- 	return function(obj) return obj:getAttr(id) end
-- end
-- local function _moai_set_attr(id)
-- 	assert(id,'no attrid')
-- 	return function(obj,v) return obj:setAttr(id, v) end
-- end

-- local function _set(id)
-- 	return function(obj,v) obj[id]=v end
-- end
-- local function _get(id)
-- 	return function(obj,v) return obj[id] end
-- end

-- local typeInfo=modelBridge:newLuaObjectType('MOAIProp')

-- typeInfo:addLuaFieldInfo('x', 'number', 
-- 		{	get = _moai_get_attr(MOAITransform.ATTR_X_LOC),
-- 			set = _moai_set_attr(MOAITransform.ATTR_X_LOC),
-- 		}
-- 	)
-- typeInfo:addLuaFieldInfo('y', 'number', 
-- 		{	get = _moai_get_attr(MOAITransform.ATTR_Y_LOC),
-- 			set = _moai_set_attr(MOAITransform.ATTR_Y_LOC),
-- 		}
-- 	)
-- typeInfo:addLuaFieldInfo('z', 'number', 
-- 		{	get = _moai_get_attr(MOAITransform.ATTR_Z_LOC),
-- 			set = _moai_set_attr(MOAITransform.ATTR_Z_LOC),
-- 		}
-- 	)

-- typeInfo:addLuaFieldInfo('sx', 'number', 
-- 		{	get = _moai_get_attr(MOAITransform.ATTR_X_SCL),
-- 			set = _moai_set_attr(MOAITransform.ATTR_X_SCL),
-- 		}
-- 	)
-- typeInfo:addLuaFieldInfo('sy', 'number', 
-- 		{	get = _moai_get_attr(MOAITransform.ATTR_Y_SCL),
-- 			set = _moai_set_attr(MOAITransform.ATTR_Y_SCL),
-- 		}
-- 	)

-- typeInfo:addLuaFieldInfo('rotation', 'number', 
-- 		{	get = _moai_get_attr(MOAITransform.ATTR_Z_ROT),
-- 			set = _moai_set_attr(MOAITransform.ATTR_Z_ROT),
-- 		}
-- 	)

-- typeInfo:addLuaFieldInfo('index', 'int', 
-- 		{	get = _method'getIndex',
-- 			set = _method'setIndex',
-- 		}
-- 	)

-- typeInfo:addLuaFieldInfo('visible', 'boolean', 
-- 		{	
-- 			get=_moai_get_attr(MOAIProp.ATTR_VISIBLE),
-- 			set=	_method'setVisible',
-- 		}
-- 	)

-- local attr_r=MOAIColor.ATTR_R_COL
-- local attr_g=MOAIColor.ATTR_G_COL
-- local attr_b=MOAIColor.ATTR_B_COL
-- local attr_a=MOAIColor.ATTR_A_COL

-- function extractColor(m)
-- 	local r = m:getAttr( attr_r )
-- 	local g = m:getAttr( attr_g )
-- 	local b = m:getAttr( attr_b )
-- 	local a = m:getAttr( attr_a )
-- 	return r,g,b,a
-- end


-- local function unpackQColor(v)
-- 	local r, g, b, a = v:redF(), v:greenF(), v:blueF(), v:alphaF()
-- 	return r, g, b, a
-- end

-- local QColor=bridge.QtGui.QColor
-- local function packQColor(r,g,b,a)
-- 	return QColor( r*255, g*255, b*255, a*255 ) 
-- end

-- local function setColorWithQtColor(obj,v)
-- 	local r,g,b,a = unpackQColor(v)
-- 	obj:setColor( r, g, b, a )
-- end

-- local function getColorAsQtColor(obj, id)
-- 	local r, g, b, a = extractColor(obj)
-- 	return packQColor( r, g, b, a )
-- end


-- typeInfo:addLuaFieldInfo('color', 'color', {
-- 		get = getColorAsQtColor,
-- 		set = setColorWithQtColor,
-- 	})

-- typeInfo:addLuaFieldInfo('name', 'string', 
-- 		{	
-- 			get = _get'name',
-- 			set = _set'name',
-- 		}
-- 	)
-- modelBridge:registerLuaObjectTypeInfo('MOAIProp', typeInfo)
-- --------------------------------------------------------------------

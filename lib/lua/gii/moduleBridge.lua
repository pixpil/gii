module('gii',package.seeall)

---Module Bridge
local function makeClosure(obj, methodName)
	return function(...) 
		local f = obj[methodName]
		return f(obj,...)
	end
end

local getinfo=debug.getinfo

local function getlevelinfo(level)
	local f=getinfo(level,'f')
	local l=-1
	if f then
		l=getinfo(level,'l').currentline
	end
	return f,l		
end

local function generateGuiID(entryFunc)
	local output=''
	lv=3
	for i=1,3 do --max 3 level
		local f,l=getlevelinfo(lv)
		output=output..'-'..l
		if f==entryFunc then break end
		lv=lv+1
	end
	return output
end

local function wrapGUIContext(context)
	local ctx={}
	local idBase=0
	local acc=context.getAccessorNames()
	local size=bridge.sizeOfPythonList(acc)
	
	for i = 0, size-1 do
		local name=acc[i]
		ctx[name]=function(...) 
			return context[name](generateGuiID(ctx.entryFunc), ...) 
		end
	end

	ctx.enter=context.enter
	ctx.exit=context.exit
	ctx.entryFunc=false
	return ctx
end

local moduleProto={}


local function makeMenuData(path, b,c)
	local option={}
	local onClick
	if type(b)=='string' then
		option.label=b
		onClick=c
	elseif type(b)=='function' then
		onClick=b
	end
	return option	, onClick
end

function moduleProto:getModule()
	return self._giiModule
end

function moduleProto:addMenu(path, ...)
	local option,onClick=makeMenuData(path, ...)
	local node=self._giiModule.addMenuItem(path, option and tableToDict(option))
	if onClick then node.setOnClick(onClick) end
end

function moduleProto:addCheckMenu(path, ...)
	local option,onClick=makeMenuData(path, ...)
	option.type='check'
	local node=self._giiModule.addMenuItem(path, option and tableToDict(option))
	if onClick then node.setOnClick(onClick) end
end

function moduleProto:setSettingValue(name, value)
	return self._giiModule.setSettingValue(path, value)
end

function moduleProto:getSettingValue(name, defvalue)
	return self._giiModule.getSettingValue(path, defvalue)
end

function moduleProto:checkMenu(path, checked)
	return self._giiModule.checkMenu(path, checked ~=false)
end



local moduleMT={
	__index=moduleProto
}

function createModule(option)
	if type(option)=='string' then
		option={name=option}
	else
		assert(option)
		assert(type(option.name)=='string')
	end
	return setmetatable(option, moduleMT)
end

function registerModule(m)
	local data={}
	
	data.name=assert(m.name , 'module name not specified')
	data.dependency=m.dep and tableToList(m.dep) or false
	data.IMGUI= m.imgui==true
	if m.onLoad then data.onLoad=makeClosure(m, 'onLoad') end
	if m.onUnload then data.onUnload=makeClosure(m, 'onUnload') end
	if m.onSerialize then data.onSerialize=makeClosure(m, 'onSerialize') end
	if m.onDeserialize then data.onDeserialize=makeClosure(m, 'onDeserialize') end
	if m.onMenu then data.onMenu=makeClosure(m, 'onMenu') end

	if m.onGUI then 
		data.onGUI=function(context)
			local ctx=m.imguiContext
			if not ctx then 
				ctx=wrapGUIContext(context)
				m.imguiContext=ctx
			end
			local func=m.onGUI
			ctx.entryFunc=func
			func(m, ctx)
			ctx.entryFunc=false
		end
	end

	local mm=bridge.registerLuaModule(data)

	m._giiModule=mm

	return mm
end

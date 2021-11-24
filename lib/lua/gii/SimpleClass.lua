module 'gii'
--gii only class support, simplified from MOCK version

--[[
* MOCK framework for Moai

* Copyright (C) 2012 Tommo Zhou(tommo.zhou@gmail.com).  All rights reserved.
*
* Permission is hereby granted, free of charge, to any person obtaining
* a copy of this software and associated documentation files (the
* "Software"), to deal in the Software without restriction, including
* without limitation the rights to use, copy, modify, merge, publish,
* distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so, subject to
* the following conditions:
*
* The above copyright notice and this permission notice shall be
* included in all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
]]

local setmetatable  = setmetatable
local getmetatable  = getmetatable

local rawget, rawset = rawget, rawset
local insert = table.insert
local type = type
local next = next
local format = string.format
--------------------------------------------------------------------
-- CLASS
--------------------------------------------------------------------
local newClass
local globalClassRegistry = setmetatable( {}, { __no_traverse = true } )

local _getLuaValueAddress
if MOCKHelper and MOCKHelper.getLuaValueAddress then
	_getLuaValueAddress = MOCKHelper.getLuaValueAddress
else
	_getLuaValueAddress = function( o )
		return tonumber( tostring( o ):sub(-10 ) )
	end
end

local buildInstanceBuilder

local reservedMembers = {
	['__init']  = true,
	['__name']  = true,
	['__env']   = true,
	['__model'] = true,
}

function getGlobalClassRegistry()
	return globalClassRegistry
end

--------------------------------------------------------------------
local BaseClass = {
	__subclasses  = {},
	__serialize   = false,
	__deserialize = false,
	__clone       = false,
}

_BASECLASS = BaseClass --use this to extract whole class tree

--Class build DSL
function BaseClass:DEPRECATED( msg )
	self.__deprecated = { msg = msg }
	return self
end

function BaseClass:rawInstance( t )
	t.__address = _getLuaValueAddress( t )
	return setmetatable( t, self )
end

function BaseClass:isSubclass( superclass )
	local s = self.__super
	while s do
		if s == superclass then return true end
		s = s.__super
	end
	return false
end

function BaseClass:isSubclassByName( superclassName )
	local s = self.__super
	while s do
		if s.__name == superclassName then return true end
		s = s.__super
	end
	return false
end

function BaseClass:isValidClass()
	return globalClassRegistry[ self.__fullname ] == self
end


--Instance Methods
function BaseClass:getClass()
	return self.__class
end

function BaseClass:getClassName()
	return self.__class.__name
end

function BaseClass:getClassSourceFile()
	return self.__class.__source
end

function BaseClass:getClassFullName()
	return self.__class.__fullname
end

function BaseClass:isInstance( clas )
	if type( clas ) == 'string' then return self:isInstanceByName( clas ) end
	local c = self.__class
	if c == clas then return true end
	return c:isSubclass( clas )
end

function BaseClass:isInstanceByName( className )
	local c = self.__class
	if c.__name == className then return true end
	return c:isSubclassByName( className )
end

function BaseClass:assertInstanceOf( superclass )
	if self:isInstance( superclass ) then
		return self 
	else
		return error( 'class not match' )
	end
end

function BaseClass:cast( clas )
	if self:isInstance( clas ) then
		return self
	else
		return nil
	end
end

function BaseClass:__repr()
	return format( '<%s:0x%08x>', self.__class.__name, self.__address or 0 )
end

function BaseClass:__tostring()
	return self:__repr()
end
----
local _methodPointerCache = setmetatable( {}, { __mode = 'kv' } )
local function _makeMethodPointer( object, methodName )
	local reg = _methodPointerCache[ object ]
	if not reg then
		reg = {}
		_methodPointerCache[ object ] = reg
	end
	local method = object.__class[ methodName ]
	if not method then
		return error( 'no method found:' .. methodName )
	end
	local mp = reg[ methodName ]
	if not mp then
		mp = function( ... )
			local func = object.__class[ methodName ]
			return func( object, ... )
		end
		reg[ methodName ] = mp
	end
	return mp
end

function BaseClass:methodPointer( methodName )
	return _makeMethodPointer( self, methodName )
end

--------------------------------------------------------------------
local function buildInitializer(class,f)
	if not class then return f end
	local init = rawget( class, '__init' )
	
	if type( init ) == 'table' then --copy
		local t1 = init
		init = function(a)
			for k,v in pairs( t1 ) do
				a[ k ] = v
			end
		end
	end

	if init then
		if f then
			local f1 = f
			f = function( a, ... )
				init( a, ... )
				return f1( a, ... )
			end
		else
			f = init
		end
	end

	local deprecated = class.__deprecated
	if deprecated then
		local f1 = f
		f = function( a, ... )
			print( 'WARNING: using DEPRECATED class:', class.__fullname, a )
			if deprecated.msg then print( deprecated.msg ) end
			print( debug.traceback(2) )
			return f1( a, ... )
		end
	end

	return buildInitializer( class.__super, f )
end


local tostring = tostring
function buildInstanceBuilder( class )
	local init = buildInitializer( class )
	local newinstance = function (t,...)
		local o = {}
		--TODO: use some C side function instead
		o.__address = _getLuaValueAddress( o )
		setmetatable( o , class )
		if init then init(o,...) end
		return o
	end

	local mt = getmetatable( class )
	mt.__call = newinstance

	for s in pairs( class.__subclasses ) do
		buildInstanceBuilder(s)
	end
end

--------------------------------------------------------------------
function newClass( b, superclass, name  )		
	b = b or {}
	local index
	superclass = superclass or BaseClass
	b.__super  = superclass

	for k,v in pairs(superclass) do --copy super method to reduce index time
		if not reservedMembers[k] and rawget(b,k)==nil then 
			b[k]=v
		end
	end

	superclass.__subclasses[b] = true

	b.__index       = b
	b.__class       = b
	b.__subclasses  = {}

	b.__no_traverse = true

	b.__repr        = superclass.__repr
	b.__tostring    = superclass.__tostring
	b.__serialize   = superclass.__serialize
	b.__deserialize = superclass.__deserialize
	b.__clone       = superclass.__clone

	if not name then
		local s = superclass
		while s do
			local sname = s.__name
			if sname and sname ~= '??' then
				name = s.__name..':??'
				break
			end
			s = s.__super
		end
	end

	b.__name  = name or '??'
	b.__classdirty = false
	--TODO: automatically spread super class modification

	local newindex=function( t, k, v )
		b.__classdirty = true
		rawset( b, k, v )
		if k=='__init' then
			buildInstanceBuilder(b)
		else --spread? TODO
		end
	end
	
	setmetatable( b, {
			__newindex = newindex,
			__isclass  = true,
			__tostring = function( t )
				return format( '<class:%s>', t.__fullname )
			end
		}
	)

	buildInstanceBuilder(b)
	if superclass.__initclass then
		superclass:__initclass( b )
	end
	return b
	
end

function updateAllSubClasses( c, force )
	for s in pairs(c.__subclasses) do
		local updated = false
		for k,v in pairs(c) do
			if not reservedMembers[k] and ( force or rawget( s, k ) == nil ) then 
				updated = true
				s[k] = v
			end
		end
		if updated then updateAllSubClasses(s) end
	end
end

function isClass( c )
	local mt = getmetatable( c )
	return mt and mt.__isclass or false
end

function isSubclass( c, super )
	if c == super then return true end
	return isClass( c ) and c:isSubclass( super )
end

function isSuperclass( c, sub )
	return isClass( sub ) and sub:isSubclass( c )
end

function isClassInstance( o )
	return getClass( o ) ~= nil
end

function isInstance( o, clas )
	return isClassInstance(o) and o:isInstance( clas )
end

function castInstance( o, clas )
	return o and isInstance( o, clas ) and o or nil
end

function assertInstanceOf( o, clas )
	if isInstance( o, clas ) then return o end
	return error( 'class not match' )
end

function getClass( o )
	if type( o ) ~= 'table' then return nil end
	local clas = getmetatable( o )
	if not clas then return nil end
	local mt = getmetatable( clas )
	return mt and mt.__isclass and clas or nil
end

local classBuilder
local function affirmClass( t, id )
	if type(id) ~= 'string' then error('class name expected',2) end

	return function( a, ... )
			local superclass
			if select( '#', ... ) >= 1 then 
				superclass = ...
				if not superclass then
					error( 'invalid superclass for:' .. id, 2 )
				end
			end
			
			if a ~= classBuilder then
				error( 'Class syntax error', 2 )
			end
			if superclass and not isClass( superclass ) then
				error( 'Superclass expected, given:'..type( superclass ), 2)
			end
			local clas = newClass( {}, superclass, id )
			local env = getfenv( 2 )
			env[ id ] = clas
			local info = debug.getinfo( 2, 'S' )
			clas.__source = info.source
			if env ~= _G then
				local prefix = env._NAME or tostring( env )
				clas.__fullname = prefix .. '.' .. clas.__name
			else
				clas.__fullname = clas.__name
			end
			clas.__env = env

			clas.__definetraceback = debug.traceback( 2 )
			local clas0 = globalClassRegistry[ clas.__fullname ]
			if clas0  then
				_error( 'duplicated class:', clas.__fullname )
				print( '-->from:',clas.__definetraceback )
				print( '-->first defined here:',clas0.__definetraceback )

			end
			globalClassRegistry[ clas.__fullname ] = clas
			return clas
		end

end

classBuilder = setmetatable( {}, { __index = affirmClass } )

local function rawClass( superclass )	
	local clas = newClass( {}, superclass, '(rawclass)' )
	clas.__fullname = clas.__name
	return clas
end

--------------------------------------------------------------------
_M.CLASS     = classBuilder

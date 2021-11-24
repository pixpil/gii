#!/usr/local/bin/lua


local input, output=...

if not input or not output then
	print(string.format('usage: mm2bt.lua <input_file.graphml> <output_file.lua>'))
	return
end

lxp = require 'lxp'

local icon2type = {
	["help"]       = "condition",
	["yes"]        = "condition_not",
	["bookmark"]   = "action",
	["full-1"]     = "priority",
	["down"]       = "sequence",
	["wizard"]     = "random",
	["knotify"]    = "shuffled",
	["stop"]       = "concurrent_and",
	["go"]         = "concurrent_or",
	["prepare"]    = "concurrent_either",
	["closed"]     = "decorator_not",
	["ksmiletris"] = "decorator_ok",
	["smily_bad"]  = "decorator_fail",
	["licq"]       = "decorator_repeat",
	["edit"]       = "commented",
}

local match = string.match
function string.trim(s)
	return match(s,'^()%s*$') and '' or match(s,'^%s*(.*%S)')
end

local insert = table.insert
local function convertMMToBT(fn)
	local callbacks={}
	
	local objects={}

	local root= false
	local edges={}

	local nodeStack={}
	local pointer=0
	local currentNode
	local prevNode

	local groupSep='.'
	local actionSep=':'

	local function pushNode(n)
		pointer=pointer+1
		nodeStack[pointer]=n
		if not root then
			root = n
		else
			local parent=currentNode or root
			local children=parent.children
			if not children then children={} parent.children=children end
			insert( children, n )
			n.parent=parent
		end
		currentNode=n
	end

	local function popNode()
		if pointer>0 then
			pointer=pointer-1
			currentNode=nodeStack[pointer]
		else
			currentNode=nil
		end
	end

	local currentGroup
	
	local function getObject(id)
		local o=objects[id]
		if not o then o={id=id} objects[id]=o end
		return o
	end

	local function CharacterData(parser,string)
		if not currentNode.value then currentNode.value=string:trim() end
	end

	function callbacks.StartElement(parser,name,attrs)
		callbacks.CharacterData=false
		if name=='node' then			
			local node = { value = attrs[ 'TEXT' ] }
			pushNode( node )
		elseif name=='icon' then
			if root == currentNode then currentNode.nodeType = 'root' return end
			local iconName = attrs['BUILTIN']
			local nodeType = icon2type [ iconName ]
			assert( nodeType , 'unknown node type(icon):'..iconName )
			currentNode.nodeType = nodeType			
		end
	end

	function callbacks.EndElement(parser,name)
		if name=='node' then
			popNode()
		end
	end

	callbacks.CharacterData=false

	local file=io.open(fn,'r')
	if not file then 
		print("file not found:",fn)
		os.exit(1)		
	end	

	local p=lxp.new(callbacks)

	for line in file:lines() do
		p:parse(line)
	end

	file:close()


	local function findchild(group,name)
		local children=group.children
		if not children then return nil end
		for c in pairs(children) do
			if c.value==name then return c end
		end
		return nil
	end

	local output = ''
	local function genNode( n )
		if not n.nodeType then error('node type invalid:'..(n.value or '???')) end
		output = output .. string.format('{ type=%q ; value=%q ;', n.nodeType or '', n.value or '' )
		if n.children and n.nodeType~='commented' then
			output = output .. ' children = {'
			for i, child in ipairs( n.children ) do
				genNode( child )
			end
			output = output .. '};'
		end
		output = output .. '};'
	end
	genNode( root )
	return output
end

function convertSingle( input, output )
	local result = convertMMToBT( input )
	local outfile=io.open(output,'w')
	outfile:write( 'return ')
	outfile:write( result )
	outfile:close()	
	return true
end

convertSingle( input, output )


-- local function stripExt(p)
-- 		 p=string.gsub(p,'%..*$','')
-- 		 return p
-- end

-- local function extractExt(p)
-- 	return string.gsub(p,'.*%.','')
-- end


-- local lfs = require"lfs"

-- local function convertAll (path,output)
-- 	local outfile=io.open(output,'w')
-- 	outfile:write('return {\n')

-- 	for filename in lfs.dir(path) do
-- 		local ext=extractExt(filename)
-- 		if ext=='mm' then
-- 			local f = path..'/'..filename
-- 			local name=stripExt(filename)
-- 			print ("\t "..f)
-- 			local attr = lfs.attributes (f)
-- 			assert (type(attr) == "table")
-- 			if attr.mode ~= "directory" then
-- 				outfile:write(string.format('[%q]=',name))
-- 				local result=convertMMToBT(f)
-- 				outfile:write(result)
-- 				outfile:write('\n')
-- 			end
-- 		end
-- 	end

-- 	outfile:write('}\n')
-- 	outfile:close()
-- end


-- convertAll(input,output)

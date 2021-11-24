--[[
	debugger hook for clidebugger
]]
module('gii',package.seeall)

local function connectDebugger()

	local commands={}
	local function readCommand(cmd,arg)
		table.insert(commands,{cmd,arg})
	end
	local function pollCommand()
		return table.remove(commands,1)
	end
	gii.connectPythonSignal('debug.command',readCommand)
	local debugging=false

	local input=function()
		if not debugging then
			gii.emitPythonSignalNow('debug.enter')
			debugging=true
		end
		while true do			
			local c=pollCommand()
			if c then
				local cmd=c[1]
				if debugging  and (
						cmd == 'step'      or
						cmd == 'over'      or
						cmd == 'out'       or
						cmd == 'exit'      or
						cmd == 'terminate' or
						cmd == 'cont' 
					)
				then
					debugging=false
					gii.emitPythonSignalNow('debug.exit')
				end
				
				if cmd=='terminate' then 
					return gii.throwPythonException("TERMINATE")
				end
				return cmd
			else
				bridge.GUIYield()
			end
		end
	end

	local output=function(...)
	end

	local send=function(msg,data)
		if data then data=MOAIJsonParser.encode(data) end
		gii.emitPythonSignal('debug.info',msg,data)
	end

	clidebugger.setupIO(input, output, send)
end

connectDebugger()

_G.debugstop=clidebugger.pause


local function gsplit(s, sep, plain )
  sep = sep or '\n'
  local start = 1
  local done = false
  local function pass(i, j, ...)
    if i then
      local seg = s:sub(start, i - 1)
      start = j + 1
      return seg, ...
    else
      done = true
      return s:sub(start)
    end
  end
  return function()
    if done then return end
    if sep == '' then done = true return s end
    return pass( s:find(sep, start, plain) )
  end
end

local match = string.match
local function trim(s)
  return match(s,'^()%s*$') and '' or match(s,'^%s*(.*%S)')
end


local function parseTuple( s )
  local t = {}
  for part in gsplit( s, ',' ) do
    part = trim( part )
    local v = tonumber( part )
    if not v then
      if part == 'true' then
        v = true
      elseif part == 'false' then
        v = false
      else
        v = part
      end
    end
    table.insert( t, v )
  end
  if #t > 1 then return t else return t[1] end
end

local function parseLine( l )
  local indent, tag, data = l:match( '( ?)(%w+): (.+)')
  if not tag then
    return 'line', l
  else
    return 'value', #indent > 0, tag, parseTuple( data )
  end
end

local function parseAtlas( data )
  local pack = {}
  local currentRegion = false
  local currentPage   = false
  for line in string.gsplit( data ) do
    local ltype, sub, tag, data = parseLine( line )
    if ltype == 'line' then
      if line == '' then --clear current page
        currentPage = false
      else 
        if not currentPage then --new pag3
          currentPage = {
            texture = line;
            regions = {}
          }
          table.insert( pack, currentPage )
        else --new region
          currentRegion = {}
          currentPage.regions[ line ] = currentRegion
        end
      end
    else
      if sub then --region
        currentRegion[ tag ] = data
      else
        currentPage[ tag ] = data
      end
    end
  end
  return pack
end

function SpineAtlas2Json( atlasName, jsonName )
  local f = io.open( atlasName, 'r' )
  local pack = parseAtlas( f:read( '*a' ) )
  f:close()
  local f1 = io.open( jsonName, 'w' )
  f1:write( MOAIJsonParser.encode( pack, 0x02 + 0x80 ) )
  f1:close()
end


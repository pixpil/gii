module 'mock_edit'

--TODO: use a global configure for this
local ColorTable   = {}
local defaultColor = { 1,1,1,1 }

function addColor( name, r,g,b,a )
	ColorTable[ name ] = {r,g,b,a}
end

function addHexColor( name, hex, alpha )
	return addColor( name, hexcolor(hex, alpha) )
end

function applyColor( name )
	MOAIDraw.setPenColor( getColor( name ) )
end

function getColorT( name, state )
	local fullname = name
	if state then
		fullname = name .. ':' .. state
		local color = ColorTable[ fullname ]
		if color then 
			return color
		end
	end
	return ColorTable[ name ] or defaultColor
end

function getColor( name, state )
	return unpack( getColorT( name, state ) )
end

module 'mock_edit'

--------------------------------------------------------------------
CLASS: TextGizmo( Gizmo )
function TextGizmo:__init( text )
	local textBox = MOAITextLabel.new()
	textBox:setStyle( mock.getFallbackTextStyle() )
	textBox:setYFlip( true )
	textBox:setAlignment( MOAITextLabel.LEFT_JUSTIFY, MOAITextLabel.BOTTOM_JUSTIFY )
	textBox:setRectLimits( false, false )

	self.textBox = textBox
	self.text = tostring( text )

	self.stylesheet = mock.loadAsset( 'font/Dialog.stylesheet' )
	if self.stylesheet then
		self.stylesheet:applyToTextBox( self.textBox, 'default' )	
	end

	self.textBox:setText( self.text )

end

function TextGizmo:onInit( target )
	if target:isInstance( mock.Entity ) then
		self:setParentEntity( target )
	elseif target._entity then
		self:setParentEntity( target._entity )
	end
end

function TextGizmo:setParentEntity( ent, propRole )
	-- self:setPickingTarget( ent )
	local prop = ent:getProp( propRole or 'render' )
	inheritLoc( self:getProp(), prop )
end

local ATTR_LOCAL_VISIBLE = MOAIProp. ATTR_LOCAL_VISIBLE
local ATTR_VISIBLE = MOAIProp. ATTR_VISIBLE

function TextGizmo:isPickable()
	return false
end

-- function TextGizmo:isPickable()
-- 	return self.pickingTarget and true or false
-- end

function TextGizmo:setText( text )
	text = tostring( text )
	self.textBox:setText( text )
end

function TextGizmo:onLoad()
	self:_attachProp( self.textBox )
end

function TextGizmo:onDestroy()
	Gizmo.onDestroy( self )
	self:_detachProp( self.textBox )
end


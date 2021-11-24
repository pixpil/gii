module 'mock_edit'

local globalGizmoIconSize = 0.7

local iconTextureCache = {}
--------------------------------------------------------------------
CLASS: IconGizmo( Gizmo )
function IconGizmo:__init( iconPath, scale )
	self.iconProp = MOAIGraphicsProp.new()
	self.iconProp:setPriority( 100 )
	setPropBlend( self.iconProp, 'alpha' )
	self.iconDeck = MOAISpriteDeck2D.new()
	self.iconProp:setDeck( self.iconDeck )	
	self.pickingTarget = false
	if iconPath then self:setIcon( iconPath, scale ) end
end

function IconGizmo:setPickingTarget( target )
	self.pickingTarget = target
end

function IconGizmo:onInit( target )
	if target:isInstance( mock.Entity ) then
		self:setParentEntity( target )
	elseif target._entity then
		self:setParentEntity( target._entity )
	end
end

function IconGizmo:onSelectStateChanged( target, state )
	if state == 'selected' then
		self.iconProp:setColor( 1, 1, 1, 1 )
	else
		self.iconProp:setColor( 1,1,1,.7 )
	end
end


local ATTR_LOCAL_VISIBLE = MOAIProp. ATTR_LOCAL_VISIBLE
local ATTR_VISIBLE = MOAIProp. ATTR_VISIBLE

function IconGizmo:setParentEntity( ent, propRole )
	self:setPickingTarget( ent )
	local prop = ent:getProp( propRole or 'render' )
	inheritLoc( self:getProp(), prop )
end

function IconGizmo:getPickingTarget()
	return self.pickingTarget
end

function IconGizmo:isPickable()
	return true
end
-- function IconGizmo:isPickable()
-- 	return self.pickingTarget and true or false
-- end

function IconGizmo:getPickingProp()
	return self.iconProp
end


function IconGizmo:setIcon( filename, scale )
	local path = gii.findDataFile( 'gizmo/'..filename )
	if not path then 
		_warn( 'gizmo icon not found', filename )
		return
	end	
	local tex = iconTextureCache[ path ]
	if not tex then
		tex = MOAITexture.new()
		tex:load( path )
		iconTextureCache[ path ] = tex
	end
	self.iconTexture = tex
	self.iconDeck:setTexture( tex )
	local w, h = tex:getSize()
	scale = ( scale or 1 ) * globalGizmoIconSize
	self.iconDeck:setRect( -w/2 * scale, -h/2 * scale, w/2 * scale, h/2 * scale )
	self.iconProp:forceUpdate()
end

function IconGizmo:onLoad()
	self:_attachProp( self.iconProp )
	self:enableConstantSize()
end

function IconGizmo:onDestroy()
	Gizmo.onDestroy( self )
	self:_detachProp( self.iconProp )
end


module 'mock_edit'
--------------------------------------------------------------------
CLASS: SimpleBoundGizmo( Gizmo )
function SimpleBoundGizmo:__init()
	self.drawBounds = false
end

function SimpleBoundGizmo:onLoad()
	self:attach( mock.DrawScript() ):setBlend( 'alpha' )
end

function SimpleBoundGizmo:onInit( target )
	self.drawBounds = target.drawBounds
end

function SimpleBoundGizmo:onDraw()
	local drawBounds = self.drawBounds
	if drawBounds then
		if self:isParentSelected() then
			applyColor 'selection_child'
		else
			applyColor 'selection'
		end
		MOAIDraw.setPenWidth(1)
		return drawBounds( self.target, self:isSelected() )
	end	
end


--------------------------------------------------------------------
--Bind to core components
local function methodBuildBoundGizmo( self )
	if self.drawBounds then		
		return SimpleBoundGizmo()
	end
end

local function installBoundGizmo( clas )
	clas.onBuildSelectedGizmo = methodBuildBoundGizmo
end


installBoundGizmo( mock.DeckComponent )
installBoundGizmo( mock.TexturePlane  )
installBoundGizmo( mock.TextLabel     )
installBoundGizmo( mock.SubTexturePlane )
installBoundGizmo( mock.MSprite       )


module 'mock_edit'
--------------------------------------------------------------------
CLASS: DrawScriptGizmo( Gizmo )
function DrawScriptGizmo:__init()
	self.target = false
	self.onDrawGizmo = false
end

function DrawScriptGizmo:onLoad()
	self:attach( mock.DrawScript() ):setBlend( 'alpha' )
end

function DrawScriptGizmo:onInit( target )
	self.onDrawGizmo = target.onDrawGizmo
end

function DrawScriptGizmo:onDraw()
	local onDrawGizmo = self.onDrawGizmo
	if onDrawGizmo then
		applyColor 'selection'
		MOAIDraw.setPenWidth(1)
		return onDrawGizmo( self.target, self:isSelected(), self:isParentSelected() )
	end	
end

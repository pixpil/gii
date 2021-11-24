module 'mock_edit'

--------------------------------------------------------------------
CLASS: SelectionTool ( CanvasTool )

function SelectionTool:__init()
	self.rectPickingEnabled = true
end

function SelectionTool:setRectPickingEnabled( enabled )
	self.rectPickingEnabled = enabled
	if self.pickPlane then
		self.pickPlane.allowRectPicking = self.rectPickingEnabled
	end
end

function SelectionTool:getPickPlane()
	return self.pickPlane
end

function SelectionTool:onLoad()
	local plane = self:addCanvasItem( CanvasPickPlane() )	
	self.pickPlane = plane
	self.pickPlane.allowRectPicking = self.rectPickingEnabled
	local inputDevice = plane:getView():getInputDevice()
	plane:setPickCallback( function( picked, pickingMode )
		return self:onPick( picked, pickingMode, inputDevice:getModifierKeyStates() )
	end)
end

function SelectionTool:onPick( picked, mode, modifiers )
	-- body
	if mode == 'selective' then
		local selections = {}
		for i, e in ipairs( picked ) do
			selections[ i ] = gii.tableToList{
				e, e:getFullName(), e:getClassName(), 'entity'
			}
		end
		requestSearchView {
			info = 'picking entity',
			selections = gii.tableToList( selections ),
			on_selection = function( selected )
				return self:applyPick( {selected}, modifiers)
			end,
			on_test = function( selected )
				--TODO: locate tested selection
			end
		}
	else
		return self:applyPick( picked, modifiers )
	end
	
end

function SelectionTool:applyPick( picked, modifiers )
	if modifiers.ctrl then
		gii.toggleSelection( 'scene', unpack( picked ) )

	elseif modifiers.shift then
		gii.addSelection( 'scene', unpack( picked ) )

	elseif modifiers.alt then
		gii.removeSelection( 'scene', unpack( picked ) )
	
	else
		gii.changeSelection( 'scene', unpack( picked ) )

	end
end

registerCanvasTool( 'selection', SelectionTool )

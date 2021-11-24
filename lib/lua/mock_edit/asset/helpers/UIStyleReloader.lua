module 'mock_edit'

local function onAssetModified( node )
	local currentView = getCurrentSceneView()
	if not currentView then return end
	local currentScene = currentView:getScene()

	local atype = node:getType()
	if atype == 'ui_style' then
		local UIViews = {}
		for e in pairs( currentScene.entities ) do
			if not ( e.FLAG_INTERNAL or e.FLAG_EDITOR_OBJECT ) then
				if e:isInstance( 'UIView' ) then
					UIViews[ e ] = true
				end
			end
		end
		for e in pairs( UIViews ) do
			e:refreshStyle()
			e:foreachChild( function( child )
				if child:isInstance( 'UIWidget' ) then
					if child.localStyleSheetPath then
						child:refreshStyle()
					end
				end
			end, true )
		end
	end
	
	gii.emitPythonSignal( 'scene.update' )

end

connectSignalFunc( 'asset.modified', onAssetModified )


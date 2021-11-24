module 'mock_edit'

--------------------------------------------------------------------
CLASS: TextureDragIn ( SceneViewDrag )
	:MODEL{}

function TextureDragIn:__init( path, x, y  )
	local cmd = gii.doCommand( 
		'scene_editor/create_entity', 
		{ 
			context = 'drag'
		}
	)
	local entity = cmd:getResult()
	local texturePlane = entity:attach( mock.TexturePlane() )
	entity:setName( stripdir(stripext(path)) )
	texturePlane:setTexture( path )
	texturePlane:resetSize()
	self.createdEntity = entity

end

function TextureDragIn:onStart( view, x, y )
	self:updateInstanceLoc( view, x, y )
end

function TextureDragIn:onMove( view, x, y )
	self:updateInstanceLoc( view, x, y )
end

function TextureDragIn:onStop( view )
	self.createdEntity:destroyWithChildrenNow()--FIXME: use undo
	-- gii.undoCommand()
	view:updateCanvas()
end

function TextureDragIn:updateInstanceLoc( view, x, y )
	if not self.createdEntity then return end
	x, y = view:wndToWorld( x, y )
	self.createdEntity:setWorldLoc( x, y )
	view:updateCanvas()
end

--------------------------------------------------------------------
CLASS: TextureDragInFactory ( SceneViewDragFactory )
	:MODEL{}

function TextureDragInFactory:create( view, mimeType, data, x, y )
	if mimeType ~= 'application/gii.asset-list' then return false end
	local result = {}
	for i, path in ipairs( data ) do
		local node = mock.getAssetNode( path )
		local assetType = node:getType()
		if assetType == 'texture' then
			return TextureDragIn( path, x, y )
		end
	end
	return result
end

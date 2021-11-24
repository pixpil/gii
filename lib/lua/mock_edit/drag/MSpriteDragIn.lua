module 'mock_edit'

--------------------------------------------------------------------
CLASS: MSpriteDragIn ( SceneViewDrag )
	:MODEL{}

function MSpriteDragIn:__init( path, x, y  )
	local cmd = gii.doCommand( 
		'scene_editor/create_entity', 
		{ 
			context = 'drag'
		}
	)
	local entity = cmd:getResult()
	local com = entity:attach( mock.MSprite() )
	entity:setName( stripdir(path) )
	com:setSprite( path )
	self.createdEntity = entity

end

function MSpriteDragIn:onStart( view, x, y )
	self:updateInstanceLoc( view, x, y )
end

function MSpriteDragIn:onMove( view, x, y )
	self:updateInstanceLoc( view, x, y )
end

function MSpriteDragIn:onStop( view )
	if self.createdEntity then 
		self.createdEntity:destroyWithChildrenNow() --FIXME: use undo
		-- gii.undoCommand()
		view:updateCanvas()
	end
end

function MSpriteDragIn:updateInstanceLoc( view, x, y )
	if not self.createdEntity then return end
	x, y = view:wndToWorld( x, y )
	self.createdEntity:setWorldLoc( x, y )
	view:updateCanvas()
end


--------------------------------------------------------------------
CLASS: MSpriteDragInFactory ( SceneViewDragFactory )
	:MODEL{}

function MSpriteDragInFactory:create( view, mimeType, data, x, y )
	if mimeType ~= 'application/gii.asset-list' then return false end
	local result = {}
	for i, path in ipairs( data ) do
		local node = mock.getAssetNode( path )
		local assetType = node:getType()
		if assetType:startwith( 'msprite' ) then
			return MSpriteDragIn( path, x, y )
		end
	end
	return result
end

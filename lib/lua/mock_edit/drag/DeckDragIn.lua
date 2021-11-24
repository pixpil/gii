module 'mock_edit'

--------------------------------------------------------------------
CLASS: DeckDragIn ( SceneViewDrag )
	:MODEL{}

function DeckDragIn:__init( path, x, y  )
	local cmd = gii.doCommand( 
		'scene_editor/create_entity', 
		{ 
			context = 'drag'
		}
	)
	local entity = cmd:getResult()
	local com = entity:attach( mock.DeckComponent() )
	entity:setName( stripdir(path) )
	com:setDeck( path )
	self.createdEntity = entity
end

function DeckDragIn:onStart( view, x, y )
	self:updateInstanceLoc( view, x, y )
end

function DeckDragIn:onMove( view, x, y )
	self:updateInstanceLoc( view, x, y )
end

function DeckDragIn:onStop( view )
	if self.createdEntity then 
		self.createdEntity:destroyWithChildrenNow() --FIXME: use undo
		-- gii.undoCommand()
		view:updateCanvas()
	end
end

function DeckDragIn:updateInstanceLoc( view, x, y )
	if not self.createdEntity then return end
	x, y = view:wndToWorld( x, y )
	self.createdEntity:setWorldLoc( x, y )
	view:updateCanvas()
end

--------------------------------------------------------------------
CLASS: DeckDragInFactory ( SceneViewDragFactory )
	:MODEL{}

function DeckDragInFactory:create( view, mimeType, data, x, y )
	if mimeType ~= 'application/gii.asset-list' then return false end
	local result = {}
	for i, path in ipairs( data ) do
		local node = mock.getAssetNode( path )
		local assetType = node:getType()
		if assetType:startwith( 'deck2d.' ) then
			return DeckDragIn( path, x, y )
		end
	end
	return result
end

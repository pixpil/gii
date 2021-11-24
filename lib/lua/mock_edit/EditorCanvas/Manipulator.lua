module 'mock_edit'

--------------------------------------------------------------------
CLASS: Manipulator ( EditorEntity )
	:MODEL{}

function Manipulator:__init()
	self.items  = {}
end

function Manipulator:setTarget( target )
	self.target = target
end

function Manipulator:getTarget()
	return self.target
end

function Manipulator:addCanvasItem( item )
	self.items[item] = true
	return self.parent:addCanvasItem( item )
end

function Manipulator:removeCanvasItem( item )
	self.items[item] = nil
	self.parent:removeCanvasItem( item )
end

function Manipulator:clearCanvasItems()
	for item in pairs( self.items ) do
		self.parent:removeCanvasItem( item )
	end
	self.items = {}
end

function Manipulator:onDestroy()
	self:clearCanvasItems()
end


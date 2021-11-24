--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

CLASS: AnimPreview ( mock.Entity )

function AnimPreview:onLoad()
	self.dragging = false
	self.spriteType = false
	self.sprite = false
end

function AnimPreview:showAnimSprite( path )
	if self.sprite then self:detach( self.sprite ) end

	local anim, node = mock.loadAsset( path )
	if node.type == 'msprite' then
		self.spriteType = 'msprite'
		self.sprite = self:attach( mock.MSprite() )
		self.sprite:setSprite( path )
		self.sprite:setBlend( 'alpha' )
		local names = {}
		for k in pairs( anim.animations ) do
			table.insert( names, k )
		end
		return names

	elseif node.type == 'spine' then
		self.spriteType = 'spine'
		self.sprite = self:attach( mock.SpineSpriteSimple() )
		self.sprite:setSprite( path )
		local names = {}
		for name, id in pairs( anim:getAnimationNames() ) do
			names[ id ] = name
		end
		return names
		
	end
end

function AnimPreview:setAnimClip( name )
	self.currentAnimClipLength = self.sprite:getClipLength( name )
	local state = self.sprite:play( name, MOAITimer.LOOP )
end

--------------------------------------------------------------------
preview = scn:addEntity( AnimPreview() )
--------------------------------------------------------------------

function onUpdate()
	--update UI

end
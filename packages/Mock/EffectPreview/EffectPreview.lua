--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

CLASS: EffectPreview ( mock.Entity )

function EffectPreview:onLoad()
	self:attach( mock.InputScript( { device = scn:getEditorInputDevice() }) )
	self.emitter    = false
	self.emitterEnt = false
end

function EffectPreview:showEffect( path )
	self.emitterEnt = mock.Entity()
	self:addSibling( self.emitterEnt )
	local emitter = mock.EffectEmitter()
	self.emitter = emitter
	self.emitterEnt:attach( emitter )
	emitter:setEffect( path )
	emitter:start()
end

function EffectPreview:clearEffect()
	if self.emitterEnt then
		self.emitterEnt:destroyWithChildrenNow()
		self.emitterEnt = false
		self.emitter = false		
	end	
end

function EffectPreview:onMouseDown( btn )
	if btn=='left' then 
		self.dragging = true
	end
end

function EffectPreview:onMouseUp( btn )
	if btn=='left' then 		
		self.dragging = false
	end
end

function EffectPreview:onMouseMove( x, y )
	if not self.dragging then return end
	x,y = self:wndToWorld( x, y )
	if self.emitterEnt then
		self.emitterEnt:setLoc( x, y )
	end
end

--------------------------------------------------------------------
preview = scn:addEntity( EffectPreview() )
--------------------------------------------------------------------
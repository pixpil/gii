--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------

CLASS: ParticlePreview ( mock.Entity )

function ParticlePreview:onLoad()
	self:attach( mock.InputScript( { device = scn:getEditorInputDevice() }) )
end

function ParticlePreview:showParticle( path )
	self.system = self:attach( mock.ParticleSystem() )
	self.system:setConfig( path )
	self.emitter = mock.ParticleEmitter()
	self.emitter.system = self.system
	self.emitter:setEmitterName( 'default' ) --TODO
	self:attach( self.emitter )
	self.emitter:updateEmitter()
	self.emitter:start()
	self.system:start()
end

function ParticlePreview:clearParticle()
	if self.emitter then
		self:detach( self.emitter )
		self.emitter = false
	end
	if self.system then
		self:detach( self.system )
		self.system = false
	end
end

function ParticlePreview:onMouseDown( btn )
	if btn=='left' then 
		self.dragging = true
	end
end

function ParticlePreview:onMouseUp( btn )
	if btn=='left' then 		
		self.dragging = false
	end
end

function ParticlePreview:onMouseMove( x, y )
	if not self.dragging then return end
	x,y = self:wndToWorld( x, y )
	local em = self.emitter and self.emitter.emitter
	if em then
		em:setLoc( x, y )
	end
end

--------------------------------------------------------------------
preview = scn:addEntity( ParticlePreview() )
--------------------------------------------------------------------
module 'mock_edit'

-- --------------------------------------------------------------------
-- CLASS: EffectEmitterPreviewer ( ComponentPreviewer )
-- 	:MODEL{}

-- function EffectEmitterPreviewer:__init( emitter )
-- 	self.targetEmitter = emitter
-- end

-- function EffectEmitterPreviewer:onStart()
-- 	self.targetState = self.targetEmitter:start()
-- end

-- function EffectEmitterPreviewer:onUpdate( dt )
-- 	-- self.targetState:update( dt )
-- end

-- function EffectEmitterPreviewer:onDestroy()
-- 	if self.targetState then
-- 		self.targetEmitter:stop( 'skip' )
-- 		self.targetState = false
-- 	end
-- end

-- function EffectEmitterPreviewer:onReset()
-- 	self:onDestroy()
-- 	self:onStart()
-- end

-- --------------------------------------------------------------------
-- CLASS: EffectEmitterPreviewerFactory ( ComponentPreviewerFactory )
-- 	:register( 'effect_emitter_previewer' )

-- function EffectEmitterPreviewerFactory:create( entity )
-- 	local emitter = entity:com( mock.EffectEmitter )
-- 	if not emitter then return false end
-- 	return EffectEmitterPreviewer( emitter )
-- end


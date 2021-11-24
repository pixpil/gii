module 'mock_edit'

CLASS: TransformProxy ()
	:MODEL{}


function TransformProxy:__init()
	self.proxy = MOAITransform.new()
end

function TransformProxy:setTarget( target )
	self.target = target
end

function TransformProxy:attachToTransform( trans )
	inheritTransform( self.proxy, trans )
end

function TransformProxy:syncFromTarget()
	local target, proxy = self.target, self.proxy
	target:forceUpdate()
	proxy:forceUpdate()
	self:onSyncFromTarget()
	proxy:forceUpdate()
end

function TransformProxy:syncToTarget( 
	drx, dry, drz, ssx ,ssy, ssz,
	updateTranslation, updateRotation, updateScale
	)

	local target, proxy = self.target, self.proxy
	target:forceUpdate()
	proxy:forceUpdate()
	self:onSyncToTarget( drx, dry, drz, ssx ,ssy, ssz )
	target:forceUpdate()
	if updateTranslation then
		mock.markProtoInstanceOverrided( target, 'loc' )
	end
	if updateRotation then
		mock.markProtoInstanceOverrided( target, 'rot' )
	end
	if updateScale then
		mock.markProtoInstanceOverrided( target, 'scl' )
	end
end

function TransformProxy:onSyncToTarget( drx, dry, drz, ssx ,ssy, ssz )
	local target, proxy = self.target, self.proxy
	GIIHelper.setWorldLoc( target:getProp(), proxy:getWorldLoc() )
	local sx, sy, sz = proxy:getScl()
	local rx, ry, rz = proxy:getRot()
	target:setScl( sx*ssx, sy*ssy, sz*ssz )
	target:setRot( rx+drx, ry+dry, rz+drz )
end


function TransformProxy:onSyncFromTarget()
	local target, proxy = self.target, self.proxy
	target:forceUpdate()
	GIIHelper.setWorldLoc( proxy, target:modelToWorld( target:getPiv() ) )
	proxy:setScl( target:getScl() )
	proxy:setRot( target:getRot() )
end

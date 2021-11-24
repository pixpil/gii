module 'mock_edit'

--------------------------------------------------------------------
CLASS: TBWidgetTransformProxy ( TransformProxy )
	:MODEL{}

function TBWidgetTransformProxy:onSyncToTarget( drx, dry, drz, ssx ,ssy, ssz )
	local target, proxy = self.target, self.proxy
	local x, y, z = proxy:getWorldLoc()
	target:setWorldLoc( x, y, z )
end


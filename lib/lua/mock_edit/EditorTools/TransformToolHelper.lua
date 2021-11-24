module 'mock_edit'

--------------------------------------------------------------------
--Transform Tool Helper
--------------------------------------------------------------------
CLASS: TransformToolHelper( EditorEntity )

function TransformToolHelper:__init()
	self.updateNode = MOAIScriptNode.new()	
	self.syncing = false
	self.updateTranslation = true
	self.updateRotation    = true
	self.updateScale       = true
end

function TransformToolHelper:setUpdateMasks( translation, rotation, scale )
	self.updateTranslation = translation or false
	self.updateRotation    = rotation    or false
	self.updateScale       = scale       or false
end

function TransformToolHelper:setTargets( targets )
	self.targets = targets
	local proxies = {}
	self.proxies = proxies

	local count = 0
	local prop  = self._prop
	for e in pairs( targets ) do		
		local proxy = e:_createTransformProxy() or TransformProxy()
		proxy:setTarget( e )
		proxies[ e ] = proxy
		proxy:attachToTransform( prop )
		count = count + 1
	end
	self.targetCount = count
	self:updatePivot()
	self:preTransform()
	self.updateNode:setCallback(
		function()
			self:onUpdate()
		end )
	self.updateNode:setNodeLink( self._prop )
end

function TransformToolHelper:forceUpdate()
	self.updateNode:forceUpdate()
end

function TransformToolHelper:preTransform()
	self:syncFromTarget()
	self.scl0 = {self:getScl()}
	self.rot0 = {self:getRot()}
end

function TransformToolHelper:updatePivot()
	if self.syncing then return end
	self.syncing = true
	local count = self.targetCount
	if count <=0 then return end
	local totalX, totalY, totalZ = 0, 0, 0
	for entity in pairs( self.targets ) do
		entity:forceUpdate()		
		local x1,y1,z1 = entity:modelToWorld( entity:getPiv() )
		totalX = totalX + x1
		totalY = totalY + y1
		totalZ = totalZ + z1
	end
	self:setLoc( totalX/count, totalY/count, totalZ/count )	

	local r0
	if count == 1 then
		r0 = next( self.targets ):getRotZ()
	else
		r0 = 0
	end
	self:setRotZ( r0 )
	self:forceUpdate()
	self.syncing = false
end

function TransformToolHelper:syncFromTarget()
	self.syncing = true
	self:forceUpdate()
	for entity, proxy in pairs( self.proxies ) do
		proxy:syncFromTarget()
	end
	self.syncing = false
end


function TransformToolHelper:onUpdate()
	if self.syncing then return end
	self.syncing = true
	self:forceUpdate()
	local rx0, ry0, rz0 = unpack( self.rot0 )
	local sx0, sy0, sz0 = unpack( self.scl0 )
	local sx1, sy1, sz1 = self:getScl()
	local rx1, ry1, rz1 = self:getRot()
	local ssx, ssy, ssz = 0, 0, 0
	if sx1 ~= 0 then ssx = sx1/sx0 end
	if sy1 ~= 0 then ssy = sy1/sy0 end
	if sz1 ~= 0 then ssz = sz1/sz0 end
	local drx, dry, drz = rx1 - rx0, ry1 - ry0, rz1 - rz0
	local updateTranslation = self.updateTranslation
	local updateRotation    = self.updateRotation
	local updateScale       = self.updateScale
	for entity, proxy in pairs( self.proxies ) do
		proxy:syncToTarget(
			drx, dry, drz, ssx ,ssy, ssz, 
			updateTranslation, updateRotation, updateScale
		)
		gii.emitPythonSignal( 'entity.modified', entity )
	end
	self.syncing = false
end


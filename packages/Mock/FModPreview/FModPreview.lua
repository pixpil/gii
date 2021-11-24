--------------------------------------------------------------------
scn = mock_edit.createSimpleEditorCanvasScene( _M )
--------------------------------------------------------------------
CLASS: FModPreview ( mock_edit.EditorEntity )
function FModPreview:onLoad()
	self:attach( mock.InputScript{ device = scn:getEditorInputDevice() } )
	self.zoom = 1
	self.soundSource = self:attach( mock.SoundSource() )
	self.soundSource:setMinDistance( 1000000 )
	self.soundSource:setMaxDistance( 1000000 )
	self.playingEvent = false
end

function FModPreview:setEvent( path )
	if path then
		local event = mock.loadAsset( path )
		self.target = event
	else
		if self.playingEvent then
			self:togglePlaying()
		end
	end
end

function FModPreview:togglePlaying()
	if self.playingEvent then
		self:stopPlaying()
	else
		self:startPlaying()		
	end
end

function FModPreview:resetPlay()
	if self.playingEvent then
		self:stopPlaying()
	end
	self:startPlaying()		
end 

function FModPreview:stopPlaying()
	if self.playingEvent then
		-- _stat( 'stop playing preview' )
		self.playingEvent:stop()
		self.playingEvent = false
	end
	stopUpdateTimer()
end

function FModPreview:startPlaying()
	-- _stat( 'playing preview' )
	self.playingEvent = self.soundSource:playEvent2D( self.target )
	startUpdateTimer( 10 )
end


function FModPreview:onMouseDown( btn )
	if btn == 'left' then
		self:resetPlay()
	elseif btn == 'right' then
		self:stopPlaying()
	end
end


function FModPreview:onUpdate()
	if self.playingEvent and not self.playingEvent:isValid() then
		self:stopPlaying()
	end
end


-- function FModPreview:onMouseMove( x, y )
-- 	if self.dragging then
-- 		local x0, y0 = unpack( self.dragFrom )
-- 		local dx, dy = x - x0, y - y0
-- 		scn.camera:setLoc( dx, -dy )
-- 		updateCanvas()
-- 	end
-- end


preview = scn:addEntity( FModPreview() )

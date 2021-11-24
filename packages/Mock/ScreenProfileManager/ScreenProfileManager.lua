CLASS: ScreenProfileManager ( mock_edit.EditorEntity )
	:MODEL{}

function ScreenProfileManager:addProfile()
	local p = mock.ScreenProfile()
	p.name = 'unamed_profile'
	p.width  = 640
	p.height = 960
	mock.registerScreenProfile( p )	
	return p
end

function ScreenProfileManager:removeProfile( p )
	mock.unregisterScreenProfile( p )
end

function ScreenProfileManager:getProfiles()
	return mock.getScreenProfileRegistry()
end

manager = ScreenProfileManager()


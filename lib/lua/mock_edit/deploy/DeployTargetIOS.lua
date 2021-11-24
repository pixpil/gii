module 'mock_edit'

EnumOrientationMode = {
	{ 'landscape', 'landscape' },
	{ 'portrait',  'portrait'  },
	{ 'both',      'both'      },
}

EnumDeviceType = {
	{ 'iPad',      'ipad'      },
	{ 'iPhone',    'iphone'    },
	{ 'Universal', 'universal' },
}

CLASS: DeployTargetIOS ( DeployTarget )
	:MODEL{
		Field 'bundleId'     :string() :label('Bundle ID');
		Field 'appName'      :string() :label('App Name');		
		Field 'device'       :enum( EnumDeviceType ) :label( 'Device' );
		Field 'orientation'  :enum( EnumOrientationMode ) :label( 'Orientation' );
	}

function DeployTargetIOS:__init()
	self.name         = 'IOS_TARGET'
	self.device       = 'universal'
	self.bundleId     = 'com.hatrix.gii_game'
	self.appName      = 'GII Game'
	self.orientation = 'portrait'
end

function DeployTargetIOS:getIcon()
	return 'ios'
end

function DeployTargetIOS:getType()
	return 'iOS'
end


registerDeployTargetType( 'iOS', DeployTargetIOS )

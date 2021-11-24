#include "MOAIJoystickFFBSensorSDL.h"


//----------------------------------------------------------------//
int MOAIJoystickFFBSensorSDL::_getVibration ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickFFBSensorSDL, "U" )	
	state.Push( self->mStrengthLeft );
	state.Push( self->mStrengthRight );
	return 2;
}

//----------------------------------------------------------------//
int MOAIJoystickFFBSensorSDL::_setVibration ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickFFBSensorSDL, "UNN" )	
	float left   = state.GetValue< float > ( 2, 1.0f );
	float right  = state.GetValue< float > ( 3, 1.0f );
	state.Push( self->SetVibration( left, right ) );
	return 1;
}

//----------------------------------------------------------------//
int MOAIJoystickFFBSensorSDL::_playRumble ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickFFBSensorSDL, "UNN" )	
	float value  = state.GetValue< float > ( 2, 1.0f );
	float length = state.GetValue< float > ( 3, 1.0f );
	self->PlayRumble( value, length );
	return 0;
}

//----------------------------------------------------------------//
int MOAIJoystickFFBSensorSDL::_stopRumble ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickFFBSensorSDL, "U" )	
	self->StopRumble();
	return 0;
}

//----------------------------------------------------------------//
int MOAIJoystickFFBSensorSDL::_isSupported ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickFFBSensorSDL, "U" )	
	if( self->mSDLHaptic ) {
		state.Push( true );
	} else {
		state.Push( false );
	}
	return 1;
}



//----------------------------------------------------------------//
MOAIJoystickFFBSensorSDL::MOAIJoystickFFBSensorSDL () :
	mSDLHaptic    ( 0 ),
	mStrengthLeft ( 0.0f ),
	mStrengthRight( 0.0f ),
	mEffectID     ( -1 )
{
	RTTI_BEGIN
		RTTI_EXTEND ( MOAISensor )
	RTTI_END
}

MOAIJoystickFFBSensorSDL::~MOAIJoystickFFBSensorSDL () {
	if( this->mSDLHaptic ) {
		SDL_HapticStopAll( this->mSDLHaptic );
		SDL_HapticClose( this->mSDLHaptic );
	}
}


//----------------------------------------------------------------//

void MOAIJoystickFFBSensorSDL::RegisterLuaClass ( MOAILuaState& state ) {
	MOAISensor::RegisterLuaClass ( state );
	
	state.SetField ( -1, "LEFT_LARGE",	( u32 )LEFT_LARGE );
	state.SetField ( -1, "LEFT_SMALL",	( u32 )LEFT_SMALL );
	state.SetField ( -1, "RIGHT_LARGE",	( u32 )RIGHT_LARGE );
	state.SetField ( -1, "RIGHT_SMALL",	( u32 )RIGHT_SMALL );

}

void MOAIJoystickFFBSensorSDL::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAISensor::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "isSupported",				_isSupported  },
		{ "setVibration",				_setVibration },
		{ "getVibration",				_getVibration },
		{ "stopVibration",			_setVibration },
		{ "playRumble",					_playRumble   },
		{ "stopRumble",					_stopRumble   },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
void MOAIJoystickFFBSensorSDL::ParseEvent ( ZLStream& eventStream ) {
	UNUSED( eventStream );
}

bool MOAIJoystickFFBSensorSDL::Init( SDL_Joystick* joystick ) {
	SDL_Haptic* haptic = SDL_HapticOpenFromJoystick( joystick );
	this->mSDLHaptic = haptic;
	if( haptic ) {
		// printf( "haptic capability: %d\n", SDL_HapticQuery( haptic ) );
		// printf( "haptic axes: %d\n", SDL_HapticNumAxes( haptic ) );
		SDL_HapticRumbleInit( haptic );
		return true;
	} else {
		// printf( "no haptic support\n" );
		return false;
	}
}

void MOAIJoystickFFBSensorSDL::PlayRumble( float strength, float length ) {
	if( !this->mSDLHaptic ) return ;
	SDL_HapticRumblePlay( this->mSDLHaptic, strength, length*1000 );
}

void MOAIJoystickFFBSensorSDL::StopRumble() {
	if( !this->mSDLHaptic ) return ;
	SDL_HapticRumbleStop( this->mSDLHaptic );
}

//CODE borrowed from LOVE ( https://www.love2d.org )
bool MOAIJoystickFFBSensorSDL::SetVibration( float left, float right ) {
	if( !this->mSDLHaptic ) return false;
	left  = std::min( std::max( left,  0.0f ), 1.0f );
	right = std::min( std::max( right, 0.0f ), 1.0f );

	if (left == 0.0f && right == 0.0f) {
		this->StopVibration();
		return true;
	}

	bool success = false;
	u32 features = SDL_HapticQuery( this->mSDLHaptic );
	int axes = SDL_HapticNumAxes( this->mSDLHaptic );

	SDL_HapticEffect& effect = this->mEffectData;

	if ((features & SDL_HAPTIC_LEFTRIGHT) != 0)
	{
		memset( &effect, 0, sizeof(SDL_HapticEffect) );
		effect.type = SDL_HAPTIC_LEFTRIGHT;

		effect.leftright.length = SDL_HAPTIC_INFINITY;
		effect.leftright.large_magnitude = (u16)( left * 65535 );
		effect.leftright.small_magnitude = (u16)( right * 65535 );

		success = this->RunSDLHapticEffect();
	}

	// Some gamepad drivers only give support for controlling individual motors
	// through a custom FF effect.
	if ( !success && (features & SDL_HAPTIC_CUSTOM) && axes == 2 )
	{
		// NOTE: this may cause issues with drivers which support custom effects
		// but aren't similar to https://github.com/d235j/360Controller .

		memset( &effect, 0, sizeof(SDL_HapticEffect) );
		// Custom effect data is clamped to 0x7FFF in SDL.
		this->mCustomEffectData[0] = this->mCustomEffectData[2] = (u16)(left * 0x7FFF);
		this->mCustomEffectData[1] = this->mCustomEffectData[3] = (u16)(right * 0x7FFF);

		effect.type = SDL_HAPTIC_CUSTOM;

		effect.custom.length = SDL_HAPTIC_INFINITY;
		effect.custom.channels = 2;
		effect.custom.period = 10;
		effect.custom.samples = 2;
		effect.custom.data = this->mCustomEffectData;

		success = this->RunSDLHapticEffect();
	}

	// Fall back to a simple sine wave if all else fails. This only supports a
	// single strength value.
	if (!success && (features & SDL_HAPTIC_SINE) != 0)
	{
		memset( &effect, 0, sizeof(SDL_HapticEffect) );
		effect.type = SDL_HAPTIC_SINE;

		effect.custom.length = SDL_HAPTIC_INFINITY;
		effect.periodic.period = 10;

		effect.periodic.magnitude = (u16)( std::max(left, right) * 0x7FFF );

		success = this->RunSDLHapticEffect();
	}

	if (success)
	{
		this->mStrengthLeft = left;
		this->mStrengthRight = right;
	}
	else
	{
		this->mStrengthLeft = 0.0f;
		this->mStrengthRight = 0.0f;
	}

	return success;
}

bool MOAIJoystickFFBSensorSDL::RunSDLHapticEffect () {
	if ( this->mEffectID != -1 ) { //update only 
		if ( SDL_HapticUpdateEffect( this->mSDLHaptic, this->mEffectID, &this->mEffectData ) == 0 )
		{
			if ( SDL_HapticRunEffect( this->mSDLHaptic, this->mEffectID, 1 ) == 0)
				return true;
		}

		// If the this->mEffectData fails to update, we should destroy and re-create it.
		SDL_HapticDestroyEffect( this->mSDLHaptic, this->mEffectID );
		this->mEffectID = -1;
	}
	
	this->mEffectID = SDL_HapticNewEffect( this->mSDLHaptic, &this->mEffectData );
	
	if ( this->mEffectID == -1 ) return false;
	return SDL_HapticRunEffect( this->mSDLHaptic, this->mEffectID, 1 ) == 0;
}

void MOAIJoystickFFBSensorSDL::StopVibration() {
	if( !this->mSDLHaptic ) return ;
	SDL_HapticStopAll( this->mSDLHaptic );
	this->mStrengthLeft  = 0.0f;
	this->mStrengthRight = 0.0f;
	this->mEffectID  = -1;
}

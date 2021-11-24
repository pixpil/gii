#ifndef MOAIJOYSTICKFFBSENSORSDL_H
#define MOAIJOYSTICKFFBSENSORSDL_H

#include "moai-sim/headers.h"
#include "SDL.h"

class MOAIJoystickFFBSensorSDL :
	public MOAISensor
{
private:

	SDL_Haptic*	mSDLHaptic;
	float				mStrengthLeft;
	float				mStrengthRight;
	int					mEffectID;
	SDL_HapticEffect mEffectData;

	u16 mCustomEffectData[ 1024 ];
	bool				RunSDLHapticEffect	();

	//----------------------------------------------------------------//
	static int _isSupported					( lua_State *L );
	static int _getVibration				( lua_State *L );
	static int _setVibration				( lua_State *L );
	static int _playRumble					( lua_State *L );
	static int _stopRumble					( lua_State *L );

public:

	enum FFBChannel {
		LEFT_LARGE,
		LEFT_SMALL,
		RIGHT_LARGE,
		RIGHT_SMALL,
	};

	DECL_LUA_FACTORY ( MOAIJoystickFFBSensorSDL )
	
	MOAIJoystickFFBSensorSDL();
	~MOAIJoystickFFBSensorSDL();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

	virtual void	ParseEvent			( ZLStream& eventStream );
	
	bool				SetVibration			( float left, float right );
	void				StopVibration			();
	void				PlayRumble				( float strength, float length );
	void				StopRumble				( );
	bool				Init							( SDL_Joystick* joystick );


};

#endif

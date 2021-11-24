#ifndef	MOAIJOYSTICKMANAGERSDL_H
#define	MOAIJOYSTICKMANAGERSDL_H

#include "SDL.h"

#include <moai-sim/headers.h>
#include <moai-sim/host.h>


class MOAIJoystickInstanceSDL;
class MOAIJoystickManagerSDL;



class MOAIJoystickInstanceSDL:
	public MOAILuaObject
{
private:
	u32								mInputDeviceID;
	MOAIInputDevice*	mInputDevice;
	SDL_Joystick*			mSDLJoystick;
	STLString 				mName;
	STLString 				mGUID;

	u32		mButtonCount;
	u32		mHatCount;
	u32		mAxeCount;
	bool	mHasFFB;

	int		mButtonsSensorID;
	int		mAxesSensorID;
	int		mFFBSensorID;

	ZLLeanArray< bool >		mButtonStates;
	ZLLeanArray< float >	mAxeStates;

	static int _getButtonCount		( lua_State *L );
	static int _getAxeCount				( lua_State *L );
	static int _getHatCount				( lua_State *L );
	static int _getName						( lua_State *L );
	static int _hasFFB						( lua_State *L );
	static int _getGUID						( lua_State *L );
	static int _getInputDevice		( lua_State *L );

public:
	friend class MOAIJoystickManagerSDL;

	DECL_LUA_FACTORY ( MOAIJoystickInstanceSDL )

	MOAIJoystickInstanceSDL();
	~MOAIJoystickInstanceSDL();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

	void Init( SDL_Joystick* joy, u32 inputDeviceID );
	void Close();
	void UpdateInputEvent();
	bool IsAttached();

};


class MOAIJoystickManagerSDL:
	public ZLContextClass < MOAIJoystickManagerSDL, MOAIGlobalEventSource > 
{
private:

	enum {
		EVENT_DEVICE_ADD,
		EVENT_DEVICE_REMOVE,
	};
	
	u32 	mJoystickCount;
	u32		mInputDevicePoolStartID, mInputDevicePoolEndID;
	STLMap< u32, MOAIJoystickInstanceSDL* > mJoystickInstanceMap;

	ZLLeanStack< u32 > mAvailInputDeviceIDPool;

	MOAILuaStrongRef mOnDeviceChange;
	
	void CheckConnections ();
	MOAIJoystickInstanceSDL* FindAvailState ();

	//----------------------------------------------------------------//
	static int _getJoystickCount						( lua_State *L );
	static int _getJoystickInputDevice			( lua_State *L );
	static int _setJoystickDeviceCallback		( lua_State *L );

public:
	void	Update ();
	void	Init ();
	void	SetInputDevicePool( u32 startID, u32 endID );
	int		PopInputDeviceID ();
	DECL_LUA_SINGLETON ( MOAIJoystickManagerSDL )

	//----------------------------------------------------------------//
	MOAIJoystickManagerSDL();
	~MOAIJoystickManagerSDL();
	
	void			RegisterLuaClass	( MOAILuaState& state );
};


#endif

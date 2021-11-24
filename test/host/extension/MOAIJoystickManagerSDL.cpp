#include "MOAIJoystickManagerSDL.h"
#include "MOAIJoystickFFBSensorSDL.h"



int MOAIJoystickInstanceSDL::_getButtonCount( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickInstanceSDL, "U" )	
	state.Push( self->mButtonCount );
	return 1;
}

int MOAIJoystickInstanceSDL::_getHatCount( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickInstanceSDL, "U" )	
	state.Push( self->mHatCount );
	return 1;
}

int MOAIJoystickInstanceSDL::_getAxeCount( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickInstanceSDL, "U" )	
	state.Push( self->mAxeCount );
	return 1;
}

int MOAIJoystickInstanceSDL::_getName( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickInstanceSDL, "U" )	
	state.Push( self->mName );
	return 1;
}

int MOAIJoystickInstanceSDL::_getGUID( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickInstanceSDL, "U" )	
	state.Push( self->mGUID );
	return 1;
}

int MOAIJoystickInstanceSDL::_hasFFB( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickInstanceSDL, "U" )	
	state.Push( self->mHasFFB );
	return 1;
}

int MOAIJoystickInstanceSDL::_getInputDevice( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIJoystickInstanceSDL, "U" )	
	if( self->mInputDevice ) {
		self->mInputDevice->PushLuaUserdata( state );
		return 1;
	}
	return 0;
}

//----------------------------------------------------------------//
MOAIJoystickInstanceSDL::MOAIJoystickInstanceSDL () :
	mInputDevice( 0 ),
	mSDLJoystick( 0 ),
	mButtonCount( 0 ),
	mHatCount( 0 ),
	mAxeCount( 0 ),
	mHasFFB( false ),
	mButtonsSensorID( -1 ),
	mAxesSensorID( -1 ),
	mFFBSensorID( -1 )
{
	RTTI_BEGIN
		RTTI_EXTEND ( MOAILuaObject )
	RTTI_END
}

MOAIJoystickInstanceSDL::~MOAIJoystickInstanceSDL () {
}

//----------------------------------------------------------------//
void MOAIJoystickInstanceSDL::RegisterLuaClass ( MOAILuaState& state ) {
	UNUSED( state );
}

void MOAIJoystickInstanceSDL::RegisterLuaFuncs	( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		{ "getButtonCount", _getButtonCount },
		{ "getAxeCount",    _getAxeCount    },
		{ "getHatCount",    _getHatCount    },
		{ "getName",        _getName        },
		{ "getGUID",        _getGUID        },
		{ "hasFFB",         _hasFFB         },
		{ "getInputDevice", _getInputDevice },
		{ NULL, NULL }
	};
	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
void MOAIJoystickInstanceSDL::Close() {
	SDL_JoystickClose( this->mSDLJoystick );
	this->mSDLJoystick = NULL;
	this->mInputDevice = NULL;
	this->mInputDeviceID = 0;
}

bool MOAIJoystickInstanceSDL::IsAttached() {
	return SDL_JoystickGetAttached( this->mSDLJoystick ) == SDL_TRUE;
}

void MOAIJoystickInstanceSDL::Init( SDL_Joystick* joy, u32 inputDeviceID ) {
	this->mSDLJoystick = joy;
	this->mInputDeviceID = inputDeviceID;

	//add sensors
	u32 buttonCount = SDL_JoystickNumButtons( this->mSDLJoystick );
	u32 hatCount    = SDL_JoystickNumHats( this->mSDLJoystick );
	u32 axeCount    = SDL_JoystickNumAxes( this->mSDLJoystick );
	u32 keyboardCount = 1;
	u32 FFBCount    = 1;
	u32 accelCount  = 0;

	this->mButtonCount = buttonCount;
	this->mHatCount = hatCount;
	this->mAxeCount = axeCount;
	this->mName = SDL_JoystickName( this->mSDLJoystick );
	char GUIDStr[ 33 ];
	SDL_JoystickGetGUIDString( SDL_JoystickGetGUID( this->mSDLJoystick), GUIDStr, 33 );
	this->mGUID = GUIDStr;


	// printf("joystick sensors: button:%d, hat:%d, axe:%d, FFB:%d\n", buttonCount, hatCount, axeCount, FFBCount );
	//build input device sensors
	MOAIInputQueue& inputMgr = MOAISim::Get().GetInputMgr();
	inputMgr.SetDevice( this->mInputDeviceID, this->mName );
	this->mInputDevice = inputMgr.GetDevice( this->mInputDeviceID );
	if( !this->mInputDevice ) printf( "noinputdevice!!!! %d\n", this->mInputDeviceID );

	u32 sensorCount = keyboardCount + axeCount + FFBCount + accelCount;
	inputMgr.ReserveSensors( inputDeviceID, sensorCount );

	u32 sensorID = 0;
	//buttons
	this->mButtonsSensorID = sensorID;
	this->mButtonStates.Init( buttonCount + hatCount );
	inputMgr.SetSensor< MOAIKeyboardSensor >( inputDeviceID, sensorID, "buttons" );
	sensorID++;

	//axes
	this->mAxesSensorID = sensorID;
	this->mAxeStates.Init( axeCount );
	for( u32 i = 0; i < axeCount; ++i ) {
		char sensorName[ 256 ];
		sprintf( sensorName, "a%d", i );
		inputMgr.SetSensor< MOAIWheelSensor >( inputDeviceID, sensorID, sensorName );
		this->mAxeStates[ i ] = 0.0f;
		sensorID++;
	}

	//ffb
	this->mFFBSensorID = sensorID;
	inputMgr.SetSensor< MOAIJoystickFFBSensorSDL >( inputDeviceID, sensorID, "FFB" );
	MOAIJoystickFFBSensorSDL* FFBSensor = 
		static_cast< MOAIJoystickFFBSensorSDL* >( 
			inputMgr.GetSensor( inputDeviceID, sensorID )
		);
	if( FFBSensor->Init( this->mSDLJoystick ) ) {
		this->mHasFFB = true;
	} else {
		this->mHasFFB = false;
	}
	sensorID++;

	//acc
}

void MOAIJoystickInstanceSDL::UpdateInputEvent() {
	//update buttons
	u32 sensorID = this->mButtonsSensorID;
	for ( u32 i = 0; i < this->mButtonCount; ++i ) {
		bool down = SDL_JoystickGetButton( this->mSDLJoystick, i );
		if( this->mButtonStates[ i ] != down ) {
			this->mButtonStates[ i ] = down;
			AKUEnqueueKeyboardKeyEvent( this->mInputDeviceID, sensorID, i, down );
		}
	}
	//update hat
	//TODO

	//update axes
	for ( u32 i = 0; i < this->mAxeCount; ++i ) {
		sensorID = this->mAxesSensorID + i;
		float value = (float)SDL_JoystickGetAxis( this->mSDLJoystick, i ) / 32768.0f;
		//TODO: deadzone support?
		if( this->mAxeStates[ i ] != value ) {
			this->mAxeStates[ i ] = value;
			AKUEnqueueWheelEvent( this->mInputDeviceID, sensorID, value );
		}
	}

	//other

}

//----------------------------------------------------------------//
// manager
//----------------------------------------------------------------//
int MOAIJoystickManagerSDL::_getJoystickCount( lua_State *L ) {
	MOAILuaState state ( L );
	state.Push ( SDL_NumJoysticks() );
	return 1;
}

int MOAIJoystickManagerSDL::_getJoystickInputDevice( lua_State *L ) {
	MOAILuaState state ( L );
	u32 idx = state.GetValue< u32 >( 1, 0 );
	//TODO
	return 0;
}

int MOAIJoystickManagerSDL::_setJoystickDeviceCallback( lua_State *L ) {
	MOAILuaState state ( L );
	MOAIJoystickManagerSDL& mgr = MOAIJoystickManagerSDL::Get();
	mgr.mOnDeviceChange.SetRef ( state, 1 );
	return 0;
}

//----------------------------------------------------------------//
MOAIJoystickManagerSDL::MOAIJoystickManagerSDL () {
	this->mJoystickCount = 0;
	this->mInputDevicePoolStartID = 0;
	this->mInputDevicePoolEndID   = 0;
	RTTI_BEGIN
		RTTI_SINGLE(MOAILuaObject)
	RTTI_END
}


MOAIJoystickManagerSDL::~MOAIJoystickManagerSDL () {
	//Nothing
}


void MOAIJoystickManagerSDL::RegisterLuaClass( MOAILuaState &state ) {
	luaL_Reg regTable [] = {
		{ "getJoystickCount",		          _getJoystickCount },
		{ "getJoystickInputDevice",		    _getJoystickInputDevice },
		{ "setJoystickDeviceCallback",		_setJoystickDeviceCallback },
		{ NULL, NULL }
	};
	luaL_register ( state, 0, regTable );
}

void MOAIJoystickManagerSDL::Init() {
	SDL_InitSubSystem( SDL_INIT_JOYSTICK );
	SDL_InitSubSystem( SDL_INIT_HAPTIC );
	SDL_JoystickEventState( SDL_IGNORE );
	
}

void MOAIJoystickManagerSDL::Update() {
	this->CheckConnections();
	STLMap< u32, MOAIJoystickInstanceSDL* >::iterator it;
	for ( it = this->mJoystickInstanceMap.begin(); it!=this->mJoystickInstanceMap.end(); ++it ) {
		MOAIJoystickInstanceSDL* instance = it->second;
		if( instance ) instance->UpdateInputEvent();
	}
}

void MOAIJoystickManagerSDL::CheckConnections() {
	SDL_JoystickUpdate();
	int count = SDL_NumJoysticks();
	if ( count == this->mJoystickCount ) return;
	this->mJoystickCount = count;

	//check detached ones
	STLMap< u32, MOAIJoystickInstanceSDL* >::iterator it;
	for ( it = this->mJoystickInstanceMap.begin(); it!=this->mJoystickInstanceMap.end(); ++it ) {
		MOAIJoystickInstanceSDL* instance = it->second;
		int instanceID = it->first;
		if( instance && !instance->IsAttached() ) {
			this->mJoystickInstanceMap[ instanceID ] = 0; //FIXME: replace with proper erase
			if ( this->mOnDeviceChange ) {
				MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();
				if ( this->mOnDeviceChange.PushRef ( state )) {
					state.Push ( "remove" );
					instance->PushLuaUserdata( state );
					state.DebugCall ( 2, 0 );
				}
			}
			this->mAvailInputDeviceIDPool.Push( instance->mInputDeviceID );
			instance->Close();
			this->LuaRelease( instance );
		}
	}

	//check newly connected ones
	for( int idx = 0; idx < count ;++idx )	{
		SDL_Joystick* joy = SDL_JoystickOpen( idx );
		int instanceID =  SDL_JoystickInstanceID( joy );
		MOAIJoystickInstanceSDL* instance = this->mJoystickInstanceMap[ instanceID ];
		if ( instance && instance->mSDLJoystick == joy ) {
			//joystick already connected
			SDL_JoystickClose( joy ); //reduce ref count
		} else {
			//new connection
			int inputDeviceID = this->PopInputDeviceID();
			if( inputDeviceID >= 0 ) {
				instance = new MOAIJoystickInstanceSDL();
				instance->Init( joy, inputDeviceID );
				this->mJoystickInstanceMap[ instanceID ] = instance;
				this->LuaRetain( instance );

				if ( this->mOnDeviceChange ) {
					MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();
					if ( this->mOnDeviceChange.PushRef ( state )) {
						state.Push ( "add" );
						instance->PushLuaUserdata( state );
						state.DebugCall ( 2, 0 );
					}
				}
			} else {
				// no more input device id
				//TODO: log
				printf( " no more input device id in joystick manager pool\n" );
			}
		}
	}
}

void MOAIJoystickManagerSDL::SetInputDevicePool( u32 startID, u32 endID ) {
	this->mInputDevicePoolStartID = startID;
	this->mInputDevicePoolEndID   = endID;
	this->mAvailInputDeviceIDPool.Reset();
	for( u32 i = endID; i >= startID ; --i )
		this->mAvailInputDeviceIDPool.Push( i );
}

int MOAIJoystickManagerSDL::PopInputDeviceID() {
	if( this->mAvailInputDeviceIDPool.GetTop() == 0 ) return -1;
	return this->mAvailInputDeviceIDPool.Pop();
}



MOAIJoystickInstanceSDL* MOAIJoystickManagerSDL::FindAvailState() {
	return NULL;
}


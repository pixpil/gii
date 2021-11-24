#include "MOAIManualTimer.h"

	//----------------------------------------------------------------//
	// TODO: doxygen
int MOAIManualTimer::_doStep ( lua_State* L ) {
	MOAI_LUA_SETUP( MOAIManualTimer, "U" )	
	float step = state.GetValue< float >( 2, 0 );
	self->DoStep( step );
	return 0;
}

//================================================================//
// MOAIManualTimer
//================================================================//

//----------------------------------------------------------------//
MOAIManualTimer::MOAIManualTimer () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOAITimer )
	RTTI_END
}

//----------------------------------------------------------------//
MOAIManualTimer::~MOAIManualTimer () {
}

//----------------------------------------------------------------//
void MOAIManualTimer::RegisterLuaClass ( MOAILuaState& state ) {
	MOAITimer::RegisterLuaClass( state );
	UNUSED( state );
}

void MOAIManualTimer::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAITimer::RegisterLuaFuncs( state );
	luaL_Reg regTable [] = {
		{ "doStep",			_doStep },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

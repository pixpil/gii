#include "moai-util/pch.h"
#include "MOAIRandom.h"

extern "C" {
	#include <SFMT.h>
}

	//----------------------------------------------------------------//
	// TODO: doxygen
int MOAIRandom::_rand ( lua_State* L ) {
	MOAI_LUA_SETUP( MOAIRandom, "U" )
	
	double lower = 0.0;
	double upper = 1.0;
	
	if ( state.IsType ( 2, LUA_TNUMBER )) {
	
		upper = state.GetValue < double >( 2, 0.0 );
	
		if ( state.IsType ( 3, LUA_TNUMBER )) {
			lower = upper;
			upper = state.GetValue < double >( 3, 0.0 );
		}
	}
	
	double r = sfmt_genrand_real1 ( self->mSFMT ); // [0, 1]
	state.Push ( lower + ( r * ( upper - lower )));
	return 1;
}

//----------------------------------------------------------------//
// TODO: doxygen
int MOAIRandom::_seed ( lua_State* L ) {
	MOAI_LUA_SETUP( MOAIRandom, "UN" )
	
	u32 seed = state.GetValue < u32 >( 2, 0 );
	sfmt_init_gen_rand ( self->mSFMT, seed );
	
	return 0;
}


//================================================================//
// MOAIRandom
//================================================================//

//----------------------------------------------------------------//
MOAIRandom::MOAIRandom () {

	RTTI_BEGIN
		RTTI_EXTEND ( MOAILuaObject )
	RTTI_END
	
	this->mSFMT = ( SFMT_T* )calloc ( 1, sizeof ( SFMT_T ));
	sfmt_init_gen_rand ( this->mSFMT, ( u32 )time ( 0 ));
}

//----------------------------------------------------------------//
MOAIRandom::~MOAIRandom () {
	free ( this->mSFMT );
}

//----------------------------------------------------------------//
void MOAIRandom::RegisterLuaClass ( MOAILuaState& state ) {
	UNUSED( state );
}

void MOAIRandom::RegisterLuaFuncs ( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		{ "rand",			_rand },
		{ "seed",			_seed },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

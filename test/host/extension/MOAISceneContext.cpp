#include "MOAISceneContext.h"

//----------------------------------------------------------------//
int MOAISceneContext::_render ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISceneContext, "U" )
	self->Render();
	return 0;
}

int MOAISceneContext::_update ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISceneContext, "UN" )
	float step = state.GetValue < float >( 2, 0.0f );
	self->Update( step );
	return 0;
}

int MOAISceneContext::_makeCurrent ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISceneContext, "U" )
	self->MakeCurrent();
	return 0;
}


//----------------------------------------------------------------//
MOAISceneContext::MOAISceneContext () :
	mCurrent( false )
{
	RTTI_SINGLE( MOAILuaObject )
}

//----------------------------------------------------------------//
MOAISceneContext::~MOAISceneContext() {

}

//----------------------------------------------------------------//
void MOAISceneContext::RegisterLuaClass ( MOAILuaState& state ) {
	UNUSED( state );
}

//----------------------------------------------------------------//
void MOAISceneContext::RegisterLuaFuncs ( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		// { "render",			_render },
		// { "update",			_update },
		// { "makeCurrent",		_makeCurrent },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
void MOAISceneContext::Render() {

}

void MOAISceneContext::Update( double step ) {

}

void MOAISceneContext::MakeCurrent() {

}

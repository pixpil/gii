#include "EWBox2DFixture.h"

EWBox2DFixture::EWBox2DFixture()
{
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIBox2DFixture )
	RTTI_END
}

EWBox2DFixture::~EWBox2DFixture()
{
}

void EWBox2DFixture::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIBox2DFixture::RegisterLuaClass ( state );
}

void EWBox2DFixture::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIBox2DFixture::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ NULL, NULL }
	};
	luaL_register ( state, 0, regTable );

}


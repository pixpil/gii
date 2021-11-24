#ifndef EWBOX2DFIXTURE_H
#define EWBOX2DFIXTURE_H

#include "moai-box2d/headers.h"

class EWBox2DFixture :
	public MOAIBox2DFixture
{
public:

	EWBox2DFixture();
	~EWBox2DFixture();

	DECL_LUA_FACTORY ( EWBox2DFixture )

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif 

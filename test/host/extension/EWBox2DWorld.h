#ifndef EWBOX2DWORLD_H
#define EWBOX2DWORLD_H

#include "EWBox2DBody.h"


class EWBox2DWorld :
	public MOAIBox2DWorld
{
private:
	static int _addEWBody ( lua_State* L );

public:
	DECL_LUA_FACTORY ( EWBox2DWorld )

	EWBox2DWorld();
	~EWBox2DWorld();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif
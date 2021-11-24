#ifndef	YAKAHELPER_H
#define	YAKAHELPER_H
#include <moai-core/pch.h>
#include <moai-sim/pch.h>

#include <moai-sim/MOAIColor.h>
#include <moai-sim/MOAITransform.h>
#include <moai-sim/MOAIGrid.h>
#include <moai-sim/MOAIAction.h>

class YAKAHelper:
	public MOAIGlobalClass < YAKAHelper, MOAINode > 
{
private:
	
	//----------------------------------------------------------------//
	static int _distanceBetweenTransform ( lua_State *L );
	static int _addColor                 ( lua_State *L );
	static int _mixColor                 ( lua_State *L );
	static int _blockAction              ( lua_State *L );

public:
	
	DECL_LUA_SINGLETON ( YAKAHelper )

	//----------------------------------------------------------------//
	YAKAHelper();
	~YAKAHelper();
	
	void			RegisterLuaClass	( MOAILuaState& state );
};


#endif
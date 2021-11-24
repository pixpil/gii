#ifndef MOAISPINEATLAS_H
#define MOAISPINEATLAS_H

#include <moai-core/headers.h>
#include <moai-sim/headers.h>

#include <spine/spine.h>
#include <spine/extension.h>

//----------------------------------------------------------------//
// allow creating spine atlas with Lua interface
//----------------------------------------------------------------//


class MOAISpineAtlas:
	public virtual MOAILuaObject
{
	private:
	
		AtlasRegion*  mLastRegion;
		static int _addRegion  ( lua_State* L );
		
	public:

		Atlas*        mAtlas ;
		DECL_LUA_FACTORY( MOAISpineAtlas )

		MOAISpineAtlas();
		~MOAISpineAtlas();

		void RegisterLuaClass ( MOAILuaState& state );
		void RegisterLuaFuncs ( MOAILuaState& state );

};

#endif

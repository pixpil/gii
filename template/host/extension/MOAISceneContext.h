#ifndef MOAISCENECONTEXT_H
#define MOAISCENECONTEXT_H

#include <moai-sim/headers.h>

class MOAISceneContext :
	public virtual MOAILuaObject {
	private:
		bool mCurrent;

		static int _render( lua_State* L );
		static int _update( lua_State* L );
		static int _makeCurrent( lua_State* L );

	public:
		DECL_LUA_FACTORY ( MOAISceneContext )
		
		MOAISceneContext();
		~MOAISceneContext();

		void Render();
		void Update( double step );
		void MakeCurrent();

		void			RegisterLuaClass	( MOAILuaState& state );
		void			RegisterLuaFuncs	( MOAILuaState& state );

};

#endif
#ifndef MOAIMANUALTIMER_H
#define MOAIMANUALTIMER_H

#include "moai-sim/pch.h"
#include "moai-sim/MOAITimer.h"

//================================================================//
// MOAIRandom
//================================================================//
// TODO: doxygen
class MOAIManualTimer :
	public virtual MOAITimer{
private:
		//----------------------------------------------------------------//
		static int		_doStep		( lua_State* L );

public:
	
	DECL_LUA_FACTORY ( MOAIManualTimer )

	//----------------------------------------------------------------//
					MOAIManualTimer			();
					~MOAIManualTimer			();
	void    RegisterLuaClass ( MOAILuaState& state );
	void    RegisterLuaFuncs ( MOAILuaState& state );
};

#endif

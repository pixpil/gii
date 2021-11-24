#ifndef EWPROP_H
#define EWPROP_H

#include "moai-sim/headers.h"
#include "MOCKProp.h"
#include "EWPropRenderTransform.h"

class EWProp :
	public MOCKProp
{
private:

public:
	DECL_LUA_FACTORY ( EWProp )
	
	EWProp();
	~EWProp();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif
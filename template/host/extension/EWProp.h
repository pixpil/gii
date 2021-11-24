#ifndef EWPROP_H
#define EWPROP_H

#include "moai-sim/headers.h"
#include "MOCKProp.h"

class EWProp :
	public MOCKProp
{
private:

public:
	DECL_LUA_FACTORY ( EWProp )

	virtual void			BuildLocalToWorldMtx		( ZLAffine3D& localToWorldMtx );
	
	EWProp();
	~EWProp();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif
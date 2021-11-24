#ifndef MOCKPOLYPARTITION_H
#define MOCKPOLYPARTITION_H

#include "moai-sim/headers.h"
#include "MOCKPolyPath.h"

//----------------------------------------------------------------//
class MOCKPolyPartition :
	public virtual MOAILuaObject
{
private:
	static int _doConvexPartition   ( lua_State* L );
	static int _doTriagulation      ( lua_State* L );

	float mUnitScale;

	int GetPolyList( lua_State* L, int idx, list< TPPLPoly > &polys );
	int PushPolyList( lua_State* L, list< TPPLPoly > &polys );

public:

	DECL_LUA_FACTORY ( MOCKPolyPartition )

	MOCKPolyPartition();
	~MOCKPolyPartition();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif


#ifndef MOCKPOLYCLIPPER_H
#define MOCKPOLYCLIPPER_H

#include "moai-sim/headers.h"
#include "MOCKPolyPath.h"

//----------------------------------------------------------------//
class MOCKPolyClipper :
	public virtual MOAILuaObject
{
private:
	// static int _pushPoly ( lua_State* L );
	static int _cleanPolygons    ( lua_State* L );
	static int _executeBoolean   ( lua_State* L );
	static int _executeOffset    ( lua_State* L );
	static int _setUnitScale     ( lua_State* L );
	static int _simplifyPolygons ( lua_State* L );

	float mUnitScale;


	int GetPaths( lua_State* L, int idx, Paths &output );
	int PushPaths( lua_State* L, const Paths &paths );

public:

	GET_SET( float, UnitScale, mUnitScale );

	static const u32 CLIP_TYPE_INTERSECTION = ctIntersection;
	static const u32 CLIP_TYPE_UNION        = ctUnion;
	static const u32 CLIP_TYPE_DIFFERENCE   = ctDifference;
	static const u32 CLIP_TYPE_XOR          = ctXor;

	DECL_LUA_FACTORY ( MOCKPolyClipper )

	MOCKPolyClipper();
	~MOCKPolyClipper();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif


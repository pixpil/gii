#ifndef MOCKPOLYPATH
#define MOCKPOLYPATH

#include "moai-sim/headers.h"

#include "clipper.hpp"
#include "polypartition.h"

using namespace ClipperLib;

class MOCKPolyPath:
	public MOAITransform
{
private:
	static int _clean        ( lua_State* L );
	static int _reserve      ( lua_State* L );
	static int _reversed     ( lua_State* L );
	static int _setVert      ( lua_State* L );

	static int _initRect     ( lua_State* L );
	static int _initCircle   ( lua_State* L );
	static int _initEllipse  ( lua_State* L );

	static int _getVertCount ( lua_State* L );
	static int _getVerts     ( lua_State* L );
	static int _isInside     ( lua_State* L );

	ZLLeanArray < ZLVec3D > mVerts;

	static inline int Side ( const ZLVec3D &v0, const ZLVec3D &v1, const ZLVec3D &v );

public:
	DECL_LUA_FACTORY ( MOCKPolyPath )

	void     Reserve       ( u32 count );
	MOCKPolyPath*   Reversed      ();
	u32      GetVertCount  ();
	ZLVec3D  GetVert       ( u32 idx );
	void     SetVert       ( u32 idx, ZLVec3D vert );
	void     SetVert       ( u32 idx, float x, float y, float z );
	void     SetVert       ( u32 idx, float x, float y );

	void InitRect    ( float x0, float y0, float x1, float y1, u32 steps = 1 );
	void InitCircle  ( float x, float y, float radius, u32 steps = 8 );
	void InitEllipse ( float x, float y, float xRad, float yRad, u32 steps = 8 );

	int GetClipperPath  ( float scale, Path &output );
	int InitFromClipperPath ( float scale, const Path &input );

	int GetTPPLPoly ( TPPLPoly &poly );
	int InitFromTPPLPoly ( TPPLPoly &input );

	void BreakLongEdge ();
	void Clean ( float distance );

	bool IsInside ( ZLVec3D loc );
	
	MOCKPolyPath();
	~MOCKPolyPath();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};


#endif

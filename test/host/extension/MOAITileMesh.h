#ifndef	MOAITILEMESH_H
#define	MOAITILEMESH_H

#include <moai-core/headers.h>
#include <moai-sim/headers.h>

class MOAITileMeshSpan
{
public:
	u32 mOffset;
	u32 mCount;	
	void Init( u32 offset, u32 count ) {
		this->mOffset = offset;
		this->mCount  = count;
	};
	MOAITileMeshSpan () :mOffset(0), mCount(0) {};
};


//----------------------------------------------------------------//
class MOAITileMesh:
	public MOAIMesh
{
private:
	ZLMatrix4x4 mRetainedMtx;
	bool			mInsideGridDraw;
	u32				mTileCount;

	ZLLeanArray < MOAITileMeshSpan >	mMeshSpans;

	static int		_reserveTiles		( lua_State* L );
	static int		_setTile				( lua_State* L );

	void			PreDraw ();
	void			PostDraw ();

public:
	DECL_LUA_FACTORY ( MOAITileMesh )

	void			ReserveTiles ( u32 count );
	void			SetTile ( u32 idx, u32 offset, u32 count );

	void			PreGridDraw();
	void			PostGridDraw();
	void			DrawIndex				( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );

	MOAITileMesh  ();
	~MOAITileMesh ();
	
	void			RegisterLuaClass		( MOAILuaState& state );
	void			RegisterLuaFuncs		( MOAILuaState& state );
	
};


#endif
#ifndef MDDMAP_H
#define MDDMAP_H

#include <moai-sim/headers.h>
#include <TMPathGrid.h>
#include <MDDMapObject.h>
#include <moai-box2d/headers.h>
#include <moai-sim/MOAIPartition.h>
#include <moai-sim/MOAIPartitionResultMgr.h>

class MDDMapObject;

class MDDMap:
	public virtual MOAILuaObject
{
private:
	static int _init           ( lua_State * L ) ;
	static int _update         ( lua_State * L ) ;

	static int _getPartition   ( lua_State * L ) ;

	static int _getPathGrid    ( lua_State * L ) ;
	static int _getBaseGrid    ( lua_State * L ) ;
	static int _getFogGrid     ( lua_State * L ) ;
	static int _getWaterGrid   ( lua_State * L ) ;
	static int _getHeightGrid    ( lua_State * L ) ;
	static int _getFlagGrid    ( lua_State * L ) ;

	static int _getWorld    ( lua_State * L ) ;


	static int _getSize        ( lua_State * L ) ;
	static int _removeObject   ( lua_State * L ) ;
	static int _insertObject   ( lua_State * L ) ;
	
public:
	static const u32 TILEBIT_VISITED   = 1;
	static const u32 TILEBIT_OCCUPIED  = 2;

	static const u32 TILEMASK_VISITED   = 1 << (TILEBIT_VISITED - 1);
	static const u32 TILEMASK_OCCUPIED  = 1 << (TILEBIT_OCCUPIED - 1);

	u32 mWidth;
	u32 mHeight;
	u32 mTileSize;

	MOAILuaSharedPtr <MOAIBox2DWorld> mWorld;
	MOAILuaSharedPtr <MOAIPartition> mPartition;
	MOAILuaSharedPtr <TMPathGrid>    mPathGrid;
	MOAILuaSharedPtr <MOAIGrid>      mBaseGrid;
	MOAILuaSharedPtr <MOAIGrid>      mFogGrid;
	MOAILuaSharedPtr <MOAIGrid>      mWaterGrid;
	MOAILuaSharedPtr <MOAIGrid>      mFlagGrid;
	MOAILuaSharedPtr <MOAIGrid>      mHeightGrid;

	MOAIPartitionResultBuffer	       mPartitionResultBuffer;

	////
	void init( u32 width, u32 height, u32 tileSize, u32 partitionCellSize, u32 sliceSize );
	void update( float delta );
	void insertObject( MDDMapObject& obj );
	void removeObject( MDDMapObject& obj );

	u32  objectInCircle( STLList< MDDMapObject* >& list, float x, float y, float radius );

	inline MOAICellCoord getCellCoord( float x, float y ){
		return mBaseGrid->GetCellCoord( x, y );
	}

	inline ZLVec2D getTileLoc( u32 x, u32 y ){
		return mBaseGrid->GetTilePoint( MOAICellCoord( x, y ), MOAIGridSpace::TILE_CENTER );
	}

	////

	DECL_LUA_FACTORY ( MDDMap )

	MDDMap();
	~MDDMap();

	void  RegisterLuaClass ( MOAILuaState& state );
	void  RegisterLuaFuncs ( MOAILuaState& state );

};

#endif

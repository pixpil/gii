
#include <MDDMap.h>

//----------------------------------------------------------------//
//GLUE
int MDDMap::_getPathGrid ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	self->mPathGrid->PushLuaUserdata( state );
	return 1;
}

int MDDMap::_getBaseGrid ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	self->mBaseGrid->PushLuaUserdata( state );
	return 1;
}

int MDDMap::_getFogGrid ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	self->mFogGrid->PushLuaUserdata( state );
	return 1;
}

int MDDMap::_getWaterGrid ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	self->mWaterGrid->PushLuaUserdata( state );
	return 1;
}

int MDDMap::_getHeightGrid ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	self->mHeightGrid->PushLuaUserdata( state );
	return 1;
}

int MDDMap::_getFlagGrid ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	self->mFlagGrid->PushLuaUserdata( state );
	return 1;
}


int MDDMap::_getPartition ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	self->mPartition->PushLuaUserdata( state );
	return 1;
}

int MDDMap::_getSize ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	state.Push( self->mWidth );
	state.Push( self->mHeight );
	return 2;
}

int MDDMap::_getWorld ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "U" )
	self->mWorld->PushLuaUserdata( state );
	return 1;
}


int MDDMap::_init ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "UNNNNN" )
	u32 w = state.GetValue< u32 >( 2, 0 );
	u32 h = state.GetValue< u32 >( 3, 0 );
	u32 tileSize           = state.GetValue< u32 >( 4, 0 );
	u32 partitionCellSize  = state.GetValue< u32 >( 5, 0 );
	u32 sliceSize          = state.GetValue< u32 >( 6, 0 );
	self->init( w, h, tileSize, partitionCellSize, sliceSize );
	return 0;
}

int MDDMap::_update ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "UN" )
	float dt = state.GetValue<float>( 2, 0 );
	self->update( dt );
	return 0;
}

int MDDMap::_insertObject ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "UU" )
	MDDMapObject* obj = state.GetLuaObject< MDDMapObject >( 2, true );
	if( !obj ) return 0;	//todo: error message
	self->insertObject( *obj );
	return 0;
}

int MDDMap::_removeObject ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMap, "UU" )
	MDDMapObject* obj = state.GetLuaObject< MDDMapObject >( 2, true );
	if( !obj ) return 0;	//todo: error message
	self->removeObject( *obj );
	return 0;
}


//----------------------------------------------------------------//
//META
MDDMap::MDDMap () :
	mHeight( 0 ),
	mWidth ( 0 )
{
	RTTI_BEGIN
		RTTI_SINGLE( MDDMap )
	RTTI_END

	mPartition .Set( *this, new MOAIPartition() );
	mPathGrid  .Set( *this, new TMPathGrid() );
	mBaseGrid  .Set( *this, new MOAIGrid() );
	mFogGrid   .Set( *this, new MOAIGrid() );
	mWaterGrid .Set( *this, new MOAIGrid() );
	mFlagGrid  .Set( *this, new MOAIGrid() );
	mHeightGrid  .Set( *this, new MOAIGrid() );
	mWorld  .Set( *this, new MOAIBox2DWorld() );

}


MDDMap::~MDDMap () {
	mPartition .Set( *this, 0 );
	mPathGrid  .Set( *this, 0 );
	mBaseGrid  .Set( *this, 0 );
	mFogGrid   .Set( *this, 0 );
	mWaterGrid .Set( *this, 0 );
	mFlagGrid  .Set( *this, 0 );
	mHeightGrid  .Set( *this, 0 );
	mWorld  .Set( *this, 0 );
}

void	MDDMap::RegisterLuaClass	( MOAILuaState& state ){
	state.SetField ( -1, "TILEBIT_VISITED",  ( u32 )TILEBIT_VISITED );
	state.SetField ( -1, "TILEBIT_OCCUPIED", ( u32 )TILEBIT_OCCUPIED );
	state.SetField ( -1, "TILEMASK_VISITED",  ( u32 )TILEMASK_VISITED );
	state.SetField ( -1, "TILEMASK_OCCUPIED", ( u32 )TILEMASK_OCCUPIED );
}

void	MDDMap::RegisterLuaFuncs	( MOAILuaState& state ){
	luaL_Reg regTable [] = {
		{ "init",             _init          },
		{ "update",           _update        },
		
		{ "getPathGrid",      _getPathGrid   },
		{ "getBaseGrid",      _getBaseGrid   },
		{ "getFogGrid",       _getFogGrid    },
		{ "getWaterGrid",     _getWaterGrid  },
		{ "getFlagGrid",      _getFlagGrid   },
		{ "getHeightGrid",    _getHeightGrid },

		{ "getWorld",         _getWorld      },


		{ "getPartition",     _getPartition  },
		{ "getSize",          _getSize       },
		{ "insertObject",     _insertObject  },
		{ "removeObject",     _removeObject  },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}



//----------------------------------------------------------------//
//Functions


void MDDMap::init( u32 width, u32 height, u32 tileSize, u32 partitionCellSize, u32 sliceSize ) {
	mWidth  = width;
	mHeight = height;
	mTileSize = tileSize;
	mPathGrid->init( width, height, tileSize, tileSize, sliceSize, sliceSize ) ;

	mPartition->ReserveLevels( 2 );
	int w = ( width * tileSize  ) / partitionCellSize;
	int h = ( height * tileSize ) / partitionCellSize;
	mPartition->SetLevel( 0, partitionCellSize, w, h );
	mPartition->SetLevel( 1, partitionCellSize * 2, w/2, h/2 );

	mBaseGrid->Init( width, height, tileSize, tileSize );
	mBaseGrid->GetTileArray().Init( mBaseGrid->GetTotalCells() );
	mBaseGrid->Fill( 0 );

	mFogGrid->Init(width,height, tileSize, tileSize );
	mFogGrid->GetTileArray().Init( mFogGrid->GetTotalCells() );
	mFogGrid->Fill( 0 );

	mWaterGrid->Init(width,height, tileSize, tileSize );
	mWaterGrid->GetTileArray().Init( mWaterGrid->GetTotalCells() );
	mWaterGrid->Fill( 0 );

	mHeightGrid->Init(width,height, tileSize, tileSize );
	mHeightGrid->GetTileArray().Init( mHeightGrid->GetTotalCells() );
	mHeightGrid->Fill( 0 );

	mFlagGrid->Init(width,height, 1, 1 );
	mFlagGrid->GetTileArray().Init( mFlagGrid->GetTotalCells() );
	mFlagGrid->Fill( 0 );


}


void MDDMap::update( float delta ) {
	u32 total = mPartition->GatherProps( mPartitionResultBuffer, 0 );
	if ( total ) {
		mPartitionResultBuffer.Sort( MOAIPartitionResultBuffer::SORT_NONE );
		//pass move & object collision
		for ( u32 i = 0; i < total; i++ ) {
			//test whether inside circle
			MOAIPartitionResult* result = mPartitionResultBuffer.GetResultUnsafe( i );
			MDDMapObject* obj = result->mProp->AsType< MDDMapObject >();
			obj->update( delta, 0 );
		}
		//wall collision
		for ( u32 i = 0; i < total; i++ ) {
			//test whether inside circle
			MOAIPartitionResult* result = mPartitionResultBuffer.GetResultUnsafe( i );
			MDDMapObject* obj = result->mProp->AsType< MDDMapObject >();
			obj->update( delta, 1);
			obj->ScheduleUpdate();
		}
	}
}

void MDDMap::insertObject ( MDDMapObject& obj ) {
	if ( obj.mMap == this ) return;
	obj.mMap = this;
	mPartition->InsertProp( obj );
}

void MDDMap::removeObject ( MDDMapObject& obj ) {
	obj.mMap = 0;
	mPartition->RemoveProp( obj );
}


inline float absf( float f ) { return f > 0 ? f : - f ; }

//----------------------------------------------------------------//
bool boundsInCircle ( const ZLBox& bounds, float x, float y, float radius ) {
	float dLeft, dRight, dTop, dBottom;
	dLeft   = x - bounds.mMin.mX;
	dRight  = x - bounds.mMax.mX;	
	dTop    = y - bounds.mMin.mY;
	dBottom = y - bounds.mMax.mY;
	if( dLeft >= 0 && dTop >= 0 && dRight <= 0 && dBottom <= 0 ) return true;
	float dx = min( absf(dLeft), absf(dRight) );
	float dy = min( absf(dTop), absf(dBottom) );

	return dx*dx < radius*radius || dy*dy < radius*radius || ( dx*dx + dy*dy ) < radius*radius;
}

bool pointInCircle ( const ZLVec3D& loc, float x, float y, float radius ) {
	float dx = loc.mX - x;
	float dy = loc.mY - y;
	return dx * dx + dy * dy <= radius * radius;
}

u32 MDDMap::objectInCircle( STLList< MDDMapObject* >& list, float x, float y, float radius ) {
	ZLBox box;
	
	box.mMin.mX = x - radius;   box.mMax.mX = x + radius;
	box.mMin.mY = y - radius;   box.mMax.mY = y + radius;
	box.mMin.mZ = 0.0f;         box.mMax.mZ = 0.0f;
	
	MOAIPartitionResultBuffer& buffer = MOAIPartitionResultMgr::Get ().GetBuffer ();

	u32 total = mPartition->GatherProps ( buffer, 0, box );
	u32 final = 0;
	if ( total ) {
		buffer.Sort( MOAIPartitionResultBuffer::SORT_NONE );
		for ( u32 i = 0; i < total; i++) {
			//test whether inside circle
			MOAIPartitionResult* result = buffer.GetResultUnsafe( i );
			MDDMapObject* obj = result->mProp->AsType< MDDMapObject >();
			if( boundsInCircle( result->mBounds, x, y, radius ) ){
				final++;
				list.push_back( obj );
			}
		}
		return final;
	}

	return 0;
}


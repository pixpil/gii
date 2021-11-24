#include "MOCKPolyPath.h"

int MOCKPolyPath::_clean ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "U" )
	float distance = state.GetValue < float >( 2, 0.001f );
	self->Clean( distance );
	return 0;
}

int MOCKPolyPath::_reserve ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "UN" )
	u32 count = state.GetValue < u32 >( 2, 0 );
	self->Reserve( count );
	return 0;
}

int MOCKPolyPath::_reversed ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "U" )
	MOCKPolyPath* newPath = self->Reversed();
	newPath->PushLuaUserdata( state );
	return 1;
}

int MOCKPolyPath::_setVert ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "UNNN" )
	u32 idx = state.GetValue < u32 >( 2, 1 ) - 1; 
	float x = state.GetValue < float >( 3, 0.0f );
	float y = state.GetValue < float >( 4, 0.0f );
	float z = state.GetValue < float >( 5, 0.0f );
	self->SetVert( idx, x, y, z );
	return 0;
}

int MOCKPolyPath::_initRect ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "UN" )
	float x0 = state.GetValue < float >( 2, 0.0f );
	float y0 = state.GetValue < float >( 3, 0.0f );
	float x1 = state.GetValue < float >( 4, 0.0f );
	float y1 = state.GetValue < float >( 5, 0.0f );
	u32 steps = state.GetValue < u32 >( 6, 1 );
	self->InitRect( x0, y0, x1, y1, steps );
	return 0;
}

int MOCKPolyPath::_initCircle ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "UNNN" )
	float x = state.GetValue < float >( 2, 0.0f );
	float y = state.GetValue < float >( 3, 0.0f );
	float r = state.GetValue < float >( 4, 0.0f );
	u32 steps = state.GetValue < u32 > ( 5, 8 );
	self->InitCircle( x, y, r, steps );
	return 0;
}

int MOCKPolyPath::_initEllipse ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "UNNN" )
	float x  = state.GetValue < float >( 2, 0.0f );
	float y  = state.GetValue < float >( 3, 0.0f );
	float rx = state.GetValue < float >( 4, 0.0f );
	float ry = state.GetValue < float >( 5, 0.0f );
	u32 steps = state.GetValue < u32 > ( 6, 8 );
	self->InitEllipse( x, y, rx, ry, steps );
	return 0;
}

int MOCKPolyPath::_getVertCount ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "U" )
	u32 size = self->mVerts.Size();
	state.Push( size );
	return 1;
}

int MOCKPolyPath::_getVerts ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "U" )
	bool toWorld = state.GetValue < bool >( 2, false );
	int count = self->mVerts.Size();
	lua_createtable( L, count*2, 0 );
	ZLVec3D loc;
	if ( toWorld ) {
		const ZLAffine3D& mtx = self->GetLocalToWorldMtx();
		for( int i = 0; i < count; ++i ) {
			loc.Init( self->mVerts[ i ] );
			mtx.Transform( loc );
			state.Push( loc.mX );
			lua_rawseti( L, -2, i*2 + 1 );
			state.Push( loc.mY );
			lua_rawseti( L, -2, i*2 + 2 );
		}
	} else {
		for( int i = 0; i < count; ++i ) {
			loc.Init( self->mVerts[ i ] );
			state.Push( loc.mX );
			lua_rawseti( L, -2, i*2 + 1 );
			state.Push( loc.mY );
			lua_rawseti( L, -2, i*2 + 2 );
		}
	}
	return 1;

}

int MOCKPolyPath::_isInside ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPath, "UN" )
	ZLVec3D loc = state.GetVec3D< float >( 2 );
	state.Push( self->IsInside( loc ) );
	return 1;
}


//----------------------------------------------------------------//
void MOCKPolyPath::Reserve ( u32 count ) {
	this->mVerts.Init( count );
}


//----------------------------------------------------------------//
MOCKPolyPath* MOCKPolyPath::Reversed () {
	MOCKPolyPath* path = new MOCKPolyPath();
	int count = this->mVerts.Size();
	path->mVerts.Init( count );
	for ( u32 i = 0; i < count; ++i ) {
		path->mVerts[ count - i - 1 ] = this->mVerts[ i ];
	}
	return path;
}


//----------------------------------------------------------------//
u32 MOCKPolyPath::GetVertCount () {
	return this->mVerts.Size();
}

//----------------------------------------------------------------//
ZLVec3D MOCKPolyPath::GetVert ( u32 idx ) {
	return this->mVerts[ idx ];
}

//----------------------------------------------------------------//
void MOCKPolyPath::SetVert( u32 idx, float x, float y, float z ) {
	if ( idx < this->mVerts.Size() ) {
		this->mVerts[ idx ].Init( x, y, z );
	}
}

//----------------------------------------------------------------//
void MOCKPolyPath::SetVert( u32 idx, ZLVec3D vert ) {
	if ( idx < this->mVerts.Size() ) {
		this->mVerts[ idx ].Init( vert );
	}
}

//----------------------------------------------------------------//
void MOCKPolyPath::SetVert( u32 idx, float x, float y ) {
	this->SetVert( idx, x, y, 0.0f );
}

//----------------------------------------------------------------//
void MOCKPolyPath::InitEllipse ( float x, float y, float xRad, float yRad, u32 steps ) {
	float step = ( float )TWOPI / ( float )steps;
	float angle = ( float )PI;
	this->Reserve( steps );
	for ( u32 i = 0; i < steps; ++i, angle += step ) {
		float xx = x + ( Cos ( angle ) * xRad );
		float yy = y + ( Sin ( angle ) * yRad );
		this->SetVert( i, xx, yy );
	}
}

//----------------------------------------------------------------//
void MOCKPolyPath::InitCircle ( float x, float y, float radius, u32 steps ) {
	this->InitEllipse( x, y, radius, radius, steps );
}

//----------------------------------------------------------------//
void MOCKPolyPath::InitRect ( float x0, float y0, float x1, float y1, u32 steps ) {
	float xMin = ( x0 > x1 ) ? x1 : x0;
	float xMax = ( x0 > x1 ) ? x0 : x1;
	float yMin = ( y0 > y1 ) ? y1 : y0;
	float yMax = ( y0 > y1 ) ? y0 : y1;

	if( steps <= 1 ) {
		this->Reserve( 4 );
		//Count-clock wise
		this->SetVert( 0, xMin, yMin );
		this->SetVert( 1, xMax, yMin );
		this->SetVert( 2, xMax, yMax );
		this->SetVert( 3, xMin, yMax );
	} else {
		this->Reserve( 4 * steps );
		this->SetVert( 0 * steps, xMin, yMin );
		for( u32 i = 1; i < steps; ++i ) {
			float k = (float)i/(float)steps;
			this->SetVert( 0 * steps + i, xMin * ( 1.0f - k ) + xMax * k, yMin );
		}
		this->SetVert( 1 * steps, xMax, yMin );
		for( u32 i = 1; i < steps; ++i ) {
			float k = (float)i/(float)steps;
			this->SetVert( 1 * steps + i, xMax, yMin * ( 1.0f - k ) + yMax * k );
		}
		this->SetVert( 2 * steps, xMax, yMax );
		for( u32 i = 1; i < steps; ++i ) {
			float k = (float)i/(float)steps;
			this->SetVert( 2 * steps + i, xMax * ( 1.0f - k ) + xMin * k, yMax );
		}
		this->SetVert( 3 * steps, xMin, yMax );
		for( u32 i = 1; i < steps; ++i ) {
			float k = (float)i/(float)steps;
			this->SetVert( 3 * steps + i, xMin, yMax * ( 1.0f - k ) + yMin * k );
		}
	}
}


//----------------------------------------------------------------//
void MOCKPolyPath::BreakLongEdge () {
	//get average edge length;

}

//----------------------------------------------------------------//
void MOCKPolyPath::Clean ( float distance ) {
	float d2 = distance * distance;
	ZLLeanArray < ZLVec3D > verts0;
	ZLLeanArray < ZLVec3D > verts1;

	verts0.CloneFrom( this->mVerts );
	u32 count = verts0.Size();
	verts1.Init( count );

	if ( count < 1 ) return;

	while ( true ) {
		ZLVec3D v0 = verts0[ 0 ];
		verts1[ 0 ] = v0;
		u32 shrinked = 0;
		for ( u32 i = 1; i < count; ++i ) {
			const ZLVec3D v = verts0[ i ];
			if ( v.DistSqrd( v0 ) < d2 ) {
				// printf("Shrinked %d\n", i );
				shrinked++;
			} else {
				if ( i == count - 1 ) { //check loop
					if( v.DistSqrd( verts0[ 0 ] ) < d2 ) {
						// printf("Shrinked loop\n");
						shrinked++;
						break;
					}
				}
				verts1[ i - shrinked ] = v;
				v0.Init( v );
			}
		}

		count -= shrinked;
		if ( shrinked == 0 || count <= 1 ) {
			this->mVerts.Init( count );
			for ( u32 i = 0; i < count; ++i ) {
				this->mVerts[ i ] = verts1[ i ];
			}
			return;

		} else {
			verts0.Init( count );
			for ( u32 i = 0; i < count; ++i ) {
				verts0[ i ] = verts1[ i ];
			}
		}
	}

}

//----------------------------------------------------------------//
int MOCKPolyPath::GetClipperPath ( float scale, Path &output ) {
	this->DepNodeUpdate();
	u32 count = this->mVerts.Size();
	output.resize( 0 );
	const ZLAffine3D& mtx = this->GetLocalToWorldMtx();
	ZLVec3D loc;
	for ( u32 i = 0; i < count; ++ i ) {
		loc.Init( this->mVerts[ i ] );
		mtx.Transform ( loc );
		output.push_back( IntPoint( (int)( loc.mX * scale ), (int)( loc.mY * scale ) ) );
	}
	return count;
}

//----------------------------------------------------------------//
int MOCKPolyPath::InitFromClipperPath ( float scale, const Path &input ) {
	this->DepNodeUpdate();
	const ZLAffine3D& mtx = this->GetWorldToLocalMtx();
	ZLVec3D loc;
	u32 count = input.size();
	this->Reserve( count );
	for ( u32 i = 0; i < count; ++ i ) {
		loc.Init( (float)input[i].X / scale, (float)input[i].Y / scale, 0.0f );
		mtx.Transform( loc );
		this->SetVert( i, loc.mX, loc.mY );
	}
	return count;
}

//----------------------------------------------------------------//
int MOCKPolyPath::GetTPPLPoly ( TPPLPoly &poly ) {
	this->DepNodeUpdate();
	u32 count = this->mVerts.Size();
	poly.Init( count );
	const ZLAffine3D& mtx = this->GetLocalToWorldMtx();
	ZLVec3D loc;
	for ( u32 i = 0; i < count; ++ i ) {
		loc.Init( this->mVerts[ i ] );
		mtx.Transform ( loc );
		poly[i].x = loc.mX;
		poly[i].y = loc.mY;
	}
	if( poly.GetOrientation() == TPPL_CW ) {
		poly.SetHole( true );
	}
	return count;
}

//----------------------------------------------------------------//
int MOCKPolyPath::InitFromTPPLPoly ( TPPLPoly &poly ) {
	this->DepNodeUpdate();
	const ZLAffine3D& mtx = this->GetWorldToLocalMtx();
	ZLVec3D loc;
	u32 count = poly.GetNumPoints();
	this->Reserve( count );
	for ( u32 i = 0; i < count; ++ i ) {
		loc.Init( poly[i].x, poly[i].y, 0.0f );
		mtx.Transform( loc );
		this->SetVert( i, loc.mX, loc.mY );
	}
	return count;
}


int MOCKPolyPath::Side(const ZLVec3D &v0, const ZLVec3D &v1, const ZLVec3D &v)
{
	ZLVec3D e = v1 - v0;
	ZLVec3D f = v - v0;
	ZLVec3D n( -e.mY, e.mX, 0.0f );
	return (int)n.Dot( f );
}

//----------------------------------------------------------------//
bool MOCKPolyPath::IsInside ( ZLVec3D loc ) {
	u32 count = this->mVerts.Size();
	for( u32 i = 0; i < count; ++i ) {
		if( MOCKPolyPath::Side( this->mVerts[ i ], this->mVerts[ (i+1) % count ], loc ) < 0 ) return false;
	}
	return true;
}

//----------------------------------------------------------------//
MOCKPolyPath::MOCKPolyPath () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOAITransform )
	RTTI_END
}

MOCKPolyPath::~MOCKPolyPath () {
}


void MOCKPolyPath::RegisterLuaClass ( MOAILuaState& state ) {
	MOAITransform::RegisterLuaClass ( state );
}

void MOCKPolyPath::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAITransform::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "clean",		      _clean        },
		{ "getVerts",		    _getVerts     },
		{ "getVertCount",   _getVertCount },
		{ "initRect",		    _initRect    },
		{ "initCircle",		  _initCircle  },
		{ "initEllipse",		_initEllipse },
		{ "isInside",   		_isInside    },
		{ "reserve",		    _reserve     },
		{ "reversed",		    _reversed    },
		{ "setVert",		    _setVert     },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}


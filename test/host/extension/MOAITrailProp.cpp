#include "MOAITrailProp.h"
#include <moai-sim/MOAIVertexFormatMgr.h>

ZLVec2D CatmullRom ( const ZLVec2D& p0, const ZLVec2D& p1, const ZLVec2D& p2, const ZLVec2D& p3, float t ) {

	ZLVec2D p;

	float t2 = t * t;
	float t3 = t2 * t;
	
	p.mX = 0.5f * (
		( 2.0f * p1.mX ) +
		( -p0.mX + p2.mX ) * t +
		( 2.0f * p0.mX - 5.0f * p1.mX + 4.0f * p2.mX - p3.mX ) * t2 +
		( -p0.mX + 3.0f * p1.mX - 3.0f * p2.mX + p3.mX ) * t3
	);
	
	p.mY = 0.5f * (
		( 2.0f * p1.mY ) +
		( -p0.mY + p2.mY ) * t +
		( 2.0f * p0.mY - 5.0f * p1.mY + 4.0f * p2.mY - p3.mY ) * t2 +
		( -p0.mY + 3.0f * p1.mY - 3.0f * p2.mY + p3.mY ) * t3
	);
	
	return p;
}

//----------------------------------------------------------------//
int MOAITrailDeck::_init ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAITrailDeck, "UNN" )	
	u32   total = state.GetValue< u32 >( 2, 10 );
	float delay = state.GetValue< float >( 3, 1.0f );
	u32   step  = state.GetValue< u32 >( 4, 2 );

	self->mTotal = total * step;
	self->mShrinkDelay = delay;
	self->mSmoothSteps = step;
	self->mSpans.Init ( self->mTotal );
	self->Clear();
	return 0;
}

int MOAITrailDeck::_setParams ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAITrailDeck, "UNN" )	
	float length = state.GetValue< float >( 2, 10.0f );
	float step   = state.GetValue< float >( 3, 5.0f );
	return 0;
}

int MOAITrailDeck::_setUVRect ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAITrailDeck, "UNNNN" )	
	float u0   = state.GetValue< float >( 2, 0.0f );
	float v0   = state.GetValue< float >( 3, 0.0f );
	float u1   = state.GetValue< float >( 4, 1.0f );
	float v1   = state.GetValue< float >( 5, 1.0f );
	self->mUVs.Init( u0, v0, u1, v1 );
	return 0;
}

int MOAITrailDeck::_push ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAITrailDeck, "UNNNN" )	
	float x0   = state.GetValue< float >( 2, 0.0f );
	float y0   = state.GetValue< float >( 3, 0.0f );
	float x1   = state.GetValue< float >( 4, 1.0f );
	float y1   = state.GetValue< float >( 5, 1.0f );
	self->PushCP( ZLVec2D( x0, y0 ), ZLVec2D( x1, y1 ) );
	return 0;
}

int MOAITrailDeck::_pop ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAITrailDeck, "U" )
	self->PopTailSpan();
	return 0;
}

int MOAITrailDeck::_clear ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAITrailDeck, "U" )
	self->Clear();
	return 0;
}

//----------------------------------------------------------------//
MOAITrailDeck::MOAITrailDeck():
	mSmoothSteps ( 2 ),
	mTotal       ( 0 ),
	mHeadId      ( 0 ),
	mTailId      ( 0 ),
	mCurrentTime ( 0 ),
	mCPCount     ( 0 ),
	mShrinkDelay ( 0.1 )
{
	mUVs.Init( 0.0f, 0.0f, 1.0f, 1.0f );
	RTTI_BEGIN
		RTTI_EXTEND( MOAIDeck )
		RTTI_EXTEND( MOAIAction )
	RTTI_END
}

MOAITrailDeck::~MOAITrailDeck(){

}


void MOAITrailDeck::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIDeck   :: RegisterLuaClass( state );	
	MOAIAction :: RegisterLuaClass( state );	
}

//----------------------------------------------------------------//
void MOAITrailDeck::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAIDeck   :: RegisterLuaFuncs( state );
	MOAIAction :: RegisterLuaFuncs( state );
	
	luaL_Reg regTable [] = {
		{ "init",        _init },
		{ "setParams",   _setParams },
		{ "setUVRect",   _setUVRect },
		{ "push",        _push },
		{ "pop",         _pop },
		{ "clear",       _clear },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

ZLBox MOAITrailDeck::ComputeMaxBounds () {
	return this->GetItemBounds ( 0 );
}

ZLBox MOAITrailDeck::GetItemBounds ( u32 idx ) {
	UNUSED ( idx );
	ZLBox bounds;
	bounds.Init ( -50, 50, 50, -50, 0, 0 );
	return bounds;
}

void MOAITrailDeck::OnUpdate ( double step ) {
	mCurrentTime += step;

	if ( mTotal ) {
		for( u32 i = mTailId; i < mHeadId; i++ ) {
			u32 idx = WrapId( i );
			if( mSpans[ idx ].mTime + mShrinkDelay > mCurrentTime ) break;
			this->PopTailSpan();
		}
	}	

}

void MOAITrailDeck::DrawIndex ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();

	gfxDevice.SetVertexPreset ( MOAIVertexFormatMgr::XYZWUVC );
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );

	if ( mTotal ) {
		if( mHeadId-mTailId < 2 ) return;
		float time0    = mSpans[ WrapId( mTailId ) ].mTime;
		float timeDiff = mSpans[ WrapId( mHeadId-1 ) ].mTime - time0;
		// if( timeDiff == 0.0f ) {
		// 	printf("%d, %d\n",mHeadId, mTailId );
		// 	return;
		// }
		gfxDevice.BeginPrim ( ZGL_PRIM_TRIANGLE_STRIP );

		float vDiff = mUVs.mYMin - mUVs.mYMax;

		for( u32 i = mHeadId; i > mTailId; i-- ) {
			MOAITrailDeckSpan& span = mSpans[ WrapId( i-1 ) ];
			float timePos = span.mTime - time0;
			float k = ( timePos / timeDiff );
			float vOff = k * vDiff;

			gfxDevice.WriteVtx ( span.mP1.mX * xScl + xOff, span.mP1.mY * yScl + yOff, zOff );
			gfxDevice.WriteUV( mUVs.mXMin, vOff + mUVs.mYMax );
			gfxDevice.WriteFinalColor4b ();

			gfxDevice.WriteVtx ( span.mP2.mX * xScl + xOff, span.mP2.mY * yScl + yOff, zOff );
			gfxDevice.WriteUV( mUVs.mXMax, vOff + mUVs.mYMax );
			gfxDevice.WriteFinalColor4b ();

		}
		gfxDevice.EndPrim();
	}
}

void MOAITrailDeck::PushCP ( ZLVec2D p1, ZLVec2D p2 ) {
	float prevTime = mPrevCPTime;
	mPrevCPTime = mCurrentTime;
	for( int i = 2; i >= 0; i-- ){
		mCP1[ i+1 ] = mCP1[ i ];
		mCP2[ i+1 ] = mCP2[ i ];
	}
	mCP1[0] = p1;
	mCP2[0] = p2;
	mCPCount += 1 ;
	if( mCPCount < 4 ) return;

	int   count = mSmoothSteps;
	float step  = 1.0f/(float)count;
	float timeDiff = mCurrentTime - prevTime;
	// printf( "----\n" );
	for( int i = 1; i < count; i ++ ) {
		float k = step * (float)i;
		ZLVec2D sp1 = CatmullRom(
			mCP1[ 3 ],
			mCP1[ 2 ],
			mCP1[ 1 ],
			mCP1[ 0 ],
			k
		);

		ZLVec2D sp2 = CatmullRom(
			mCP2[ 3 ],
			mCP2[ 2 ],
			mCP2[ 1 ],
			mCP2[ 0 ],
			k
		);
		// printf( "%.0f,%.0f\n",sp1.mX, p1.mX);
		this->PushHeadSpan( sp1, sp2, timeDiff * k + prevTime );
	}
	this->PushHeadSpan( mCP1[1], mCP2[1], mCurrentTime );
}

void MOAITrailDeck::PushHeadSpan ( ZLVec2D p1, ZLVec2D p2, float t ) {
	if( mHeadId - mTailId >= mTotal ) { this->PopTailSpan();	}
	
	u32 idx = WrapId( mHeadId );
	MOAITrailDeckSpan& span = this->mSpans[ idx ];
	span.mP1 = p1;
	span.mP2 = p2;
	span.mTime = t;

	mHeadId += 1;	
}

void MOAITrailDeck::PopTailSpan () {
	if( mTailId < mHeadId ) {
		mTailId += 1;
	}
}

void MOAITrailDeck::Clear () {
	mHeadId      = 0;
	mTailId      = 0;
	mCPCount     = 0;
	mCurrentTime = 0.0f;
	mPrevCPTime  = 0.0f;
}


bool MOAITrailDeck::IsDone () {
	return false;
}

//----------------------------------------------------------------//
int MOAITrailProp::_setParams ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAITrailProp, "UNN" )	
	float length = state.GetValue< float >( 2, 10 );
	float step   = state.GetValue< float >( 3, 5 );
	return 0;
}


//----------------------------------------------------------------//
MOAITrailProp::MOAITrailProp():
	mLength ( 10 ),
	mStep   ( 5 )
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAIGraphicsProp )
		RTTI_EXTEND( MOAIAction )
	RTTI_END
}

MOAITrailProp::~MOAITrailProp(){

}


void MOAITrailProp::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIGraphicsProp   :: RegisterLuaClass( state );	
	MOAIAction :: RegisterLuaClass( state );	
}

//----------------------------------------------------------------//
void MOAITrailProp::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAIGraphicsProp   :: RegisterLuaFuncs( state );
	MOAIAction :: RegisterLuaFuncs( state );
	
	luaL_Reg regTable [] = {
		{ "setParams",				_setParams },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

void MOAITrailProp::OnUpdate ( float step ) {
}

void MOAITrailProp::Draw ( int subPrimID ) {
	UNUSED ( subPrimID );

}

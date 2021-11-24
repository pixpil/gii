// Copyright (c) 2010-2011 Zipline Games, Inc. All Rights Reserved.
// http://getmoai.com

#include "MOAIGeometry2DDeck.h"
//================================================================//
// local
//================================================================//

//----------------------------------------------------------------//
void MOAIGeometry2DDeckPrim::SetColor ( float r, float g, float b, float a ) {
	this->mColor.Set( r, g, b, a );
}


ZLBox MOAIGeometry2DDeckPrim::GetBounds () {
	ZLBox bounds;
	bounds.Init( 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f );
	return bounds;
}


//----------------------------------------------------------------//
bool MOAIGeometry2DDeckPrim::Inside ( ZLVec3D vec, float pad ) {
	return true;
}

//----------------------------------------------------------------//
//----------------------------------------------------------------//
ZLBox MOAIGeometry2DDeckPrimRect::GetBounds () {
	ZLBox bounds;
	bounds.Init( this->mRect );
	return bounds;
}

//----------------------------------------------------------------//
void MOAIGeometry2DDeckPrimRect::Draw ( float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	MOAIGfxDevice::Get ().SetPenColor ( this->mColor );
	float x0, y0, x1, y1;
	x0 = this->mRect.mXMin;
	y0 = this->mRect.mYMin;
	x1 = this->mRect.mXMax;
	y1 = this->mRect.mYMax;
	if ( this->mFilled ) {
		MOAIDraw::DrawRectFill ( 
			x0 * xScl + xOff, y0 * yScl + yOff,
			x1 * xScl + xOff, y1 * yScl + yOff
		);
	} else {
		MOAIDraw::DrawRectOutline ( 
			x0 * xScl + xOff, y0 * yScl + yOff,
			x1 * xScl + xOff, y1 * yScl + yOff
		);
	}
}



//----------------------------------------------------------------//
//----------------------------------------------------------------//
ZLBox MOAIGeometry2DDeckPrimCircle::GetBounds () {
	ZLBox bounds;
	bounds.Init(
		this->mOrigin.mX - this->mRadius, this->mOrigin.mY - this->mRadius,
		this->mOrigin.mX + this->mRadius, this->mOrigin.mY + this->mRadius,
		0.0f, 0.0f
	);
	return bounds;
}

//----------------------------------------------------------------//
void MOAIGeometry2DDeckPrimCircle::Draw ( float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	MOAIGfxDevice::Get ().SetPenColor ( this->mColor );
	if ( this->mFilled ) {
		MOAIDraw::DrawEllipseFill (
			this->mOrigin.mX * xScl + xOff, this->mOrigin.mY * yScl + yOff, 
			this->mRadius * xScl, this->mRadius * yScl,
			32
		);
	} else {
		MOAIDraw::DrawEllipseOutline (
			this->mOrigin.mX * xScl + xOff, this->mOrigin.mY * yScl + yOff, 
			this->mRadius * xScl, this->mRadius * yScl,
			32
		);
	}
}

//----------------------------------------------------------------//
bool MOAIGeometry2DDeckPrimCircle::Inside ( ZLVec3D vec, float pad ) {
	UNUSED ( pad );
	float rad = this->mRadius;
	float dist2 = this->mOrigin.DistSqrd( ZLVec2D( vec.mX, vec.mY ) );
	return dist2 <= rad * rad;
}


//----------------------------------------------------------------//
int MOAIGeometry2DDeck::_reserve ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGeometry2DDeck, "UN" )
	
	u32 size = state.GetValue < u32 >( 2, 0 );
	self->Reserve ( size );
	return 0;
}

int MOAIGeometry2DDeck::_setRect ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGeometry2DDeck, "UNNNN" )
	
	self->mRect = state.GetRect < float >( 2 );

	return 0;
}

int MOAIGeometry2DDeck::_setRectItem ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGeometry2DDeck, "UNNNN" )
	u32 idx = state.GetValue < float >( 2, 1 ) - 1;

	float x0 = state.GetValue < float >( 3, 0.0f );
	float y0 = state.GetValue < float >( 4, 0.0f );
	float x1 = state.GetValue < float >( 5, 0.0f );
	float y1 = state.GetValue < float >( 6, 0.0f );

	float r = state.GetValue < float >( 7, 1.0f );
	float g = state.GetValue < float >( 8, 1.0f );
	float b = state.GetValue < float >( 9, 1.0f );
	float a = state.GetValue < float >( 10, 1.0f );

	MOAIGeometry2DDeckPrimRect* prim = new MOAIGeometry2DDeckPrimRect ( 
		x0, y0, x1, y1, false
	);
	prim->SetColor ( r, g, b, a );

	self->SetGeometry( idx, prim );
	return 0;
}

int MOAIGeometry2DDeck::_setFilledRectItem ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGeometry2DDeck, "UNNNN" )
	u32 idx = state.GetValue < float >( 2, 1 ) - 1;

	float x0 = state.GetValue < float >( 3, 0.0f );
	float y0 = state.GetValue < float >( 4, 0.0f );
	float x1 = state.GetValue < float >( 5, 0.0f );
	float y1 = state.GetValue < float >( 6, 0.0f );

	float r = state.GetValue < float >( 7, 1.0f );
	float g = state.GetValue < float >( 8, 1.0f );
	float b = state.GetValue < float >( 9, 1.0f );
	float a = state.GetValue < float >( 10, 1.0f );

	MOAIGeometry2DDeckPrimRect* prim = new MOAIGeometry2DDeckPrimRect (  x0, y0, x1, y1, true );
	prim->SetColor ( r, g, b, a );

	self->SetGeometry( idx, prim );
	return 0;
}

int MOAIGeometry2DDeck::_setCircleItem ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGeometry2DDeck, "UNNNN" )
	u32 idx = state.GetValue < float >( 2, 1 ) - 1;

	float x = state.GetValue < float >( 3, 0.0f );
	float y = state.GetValue < float >( 4, 0.0f );
	float radius = state.GetValue < float >( 5, 0.0f );

	float r = state.GetValue < float >( 6, 1.0f );
	float g = state.GetValue < float >( 7, 1.0f );
	float b = state.GetValue < float >( 8, 1.0f );
	float a = state.GetValue < float >( 9, 1.0f );

	MOAIGeometry2DDeckPrimCircle* prim = new MOAIGeometry2DDeckPrimCircle ( x, y, radius, false );
	prim->SetColor ( r, g, b, a );

	self->SetGeometry( idx, prim );
	return 0;
}

int MOAIGeometry2DDeck::_setFilledCircleItem ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGeometry2DDeck, "UNNNN" )
	u32 idx = state.GetValue < float >( 2, 1 ) - 1;

	float x = state.GetValue < float >( 3, 0.0f );
	float y = state.GetValue < float >( 4, 0.0f );
	float radius = state.GetValue < float >( 5, 0.0f );

	float r = state.GetValue < float >( 6, 1.0f );
	float g = state.GetValue < float >( 7, 1.0f );
	float b = state.GetValue < float >( 8, 1.0f );
	float a = state.GetValue < float >( 9, 1.0f );

	MOAIGeometry2DDeckPrimCircle* prim = new MOAIGeometry2DDeckPrimCircle ( x, y, radius, true );
	prim->SetColor ( r, g, b, a );

	self->SetGeometry( idx, prim );
	return 0;
}


//================================================================//
// MOAIGeometry2DDeck
//================================================================//

//----------------------------------------------------------------//
ZLBox MOAIGeometry2DDeck::ComputeMaxBounds () {

	ZLRect rect = this->mRect;
	ZLBox bounds;
	bounds.Init ( rect.mXMin, rect.mYMax, rect.mXMax, rect.mYMin, 0.0f, 0.0f );	
	return bounds;
}


//----------------------------------------------------------------//
bool MOAIGeometry2DDeck::Inside ( u32 idx, ZLVec3D vec, float pad ) {
	idx = ( idx - 1 ) % this->mPrims.Size ();
	if ( !this->mPrims[ idx ] ) return false;
	return this->mPrims[ idx ]->Inside ( vec, pad );
}


//----------------------------------------------------------------//
void MOAIGeometry2DDeck::DrawIndex ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	UNUSED ( zOff );
	UNUSED ( zScl );
	if ( this->mPrims.Size () == 0 ) return;
	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
	gfxDevice.SetVertexPreset ( MOAIVertexFormatMgr::XYZWC );
	
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );
	
	idx = ( idx - 1 ) % this->mPrims.Size ();
	if ( this->mPrims[ idx ] ) {
		this->mPrims[ idx ]->Draw ( xOff, yOff, zOff, xScl, yScl, zScl );
	}
}

//----------------------------------------------------------------//
ZLBox MOAIGeometry2DDeck::GetItemBounds ( u32 idx ) {
	if ( this->mPrims.Size () > 0 ) {
		idx = ( idx - 1 ) % this->mPrims.Size ();
		if ( this->mPrims[ idx ] ) {
			return this->mPrims[ idx ]->GetBounds();
		}
	}
	ZLBox bounds;
	bounds.Init( 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f );
	return bounds;
}


//----------------------------------------------------------------//
void MOAIGeometry2DDeck::Reserve ( u32 size ) {
	this->mPrims.Init ( size );
	this->mPrims.Fill ( 0 );
}

void MOAIGeometry2DDeck::Clear () {
	for ( u32 i = 0; i < this->mPrims.Size (); ++i ) {
		if ( this->mPrims[ i ] ) {
			delete this->mPrims[ i ];
			this->mPrims[ i ] = 0;
		}
	}
}

void MOAIGeometry2DDeck::SetGeometry ( u32 idx, MOAIGeometry2DDeckPrim* prim ) {
	if ( idx >= this->mPrims.Size () ) return;
	if ( this->mPrims[ idx ] ) {
		delete this->mPrims[ idx ];
	}
	this->mPrims[ idx ] = prim;
}

//----------------------------------------------------------------//
MOAIGeometry2DDeck::MOAIGeometry2DDeck () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIDeck )
	RTTI_END
	
	this->mRect.Init ( 0.0f, 0.0f, 0.0f, 0.0f );
	this->mDefaultShaderID = MOAIShaderMgr::LINE_SHADER;
}

//----------------------------------------------------------------//
MOAIGeometry2DDeck::~MOAIGeometry2DDeck () {
}

//----------------------------------------------------------------//
void MOAIGeometry2DDeck::RegisterLuaClass ( MOAILuaState& state ) {
	this->MOAIDeck::RegisterLuaClass ( state );
}

//----------------------------------------------------------------//
void MOAIGeometry2DDeck::RegisterLuaFuncs ( MOAILuaState& state ) {

	this->MOAIDeck::RegisterLuaFuncs ( state );

	luaL_Reg regTable [] = {
		{ "reserve",             _reserve              },
		{ "setCircleItem",       _setCircleItem        },
		{ "setFilledCircleItem", _setFilledCircleItem  },
		{ "setFilledRectItem",   _setFilledRectItem    },
		{ "setRect",             _setRect              },
		{ "setRectItem",         _setRectItem          },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}
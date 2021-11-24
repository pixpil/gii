// Copyright (c) 2010-2011 Zipline Games, Inc. All Rights Reserved.
// http://getmoai.com

#include <moai-sim/pch.h>
#include <moai-sim/MOAIDeckRemapper.h>
#include <moai-sim/MOAIGrid.h>
#include <moai-sim/MOAIProp.h>
#include <moai-sim/MOAITextureBase.h>
#include <moai-sim/MOAITransformBase.h>

#include "MOAIGfxMaskedQuadListDeck2D.h"

//================================================================//
// local
//================================================================//

//----------------------------------------------------------------//
/**	@lua	reserveLists
	@text	Reserve quad lists.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number nLists
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_reserveLists ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UN" )

	u32 total = state.GetValue < u32 >( 2, 0 );
	self->ReserveLists ( total );

	return 0;
}

//----------------------------------------------------------------//
/**	@lua	reservePairs
	@text	Reserve pairs.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number nPairs
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_reservePairs ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UN" )

	u32 total = state.GetValue < u32 >( 2, 0 );
	self->ReservePairs ( total );

	return 0;
}

//----------------------------------------------------------------//
/**	@lua	reserveQuads
	@text	Reserve quads.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number nQuads
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_reserveQuads ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UN" )

	u32 total = state.GetValue < u32 >( 2, 0 );
	self->ReserveQuads ( total );

	return 0;
}

//----------------------------------------------------------------//
/**	@lua	reserveUVQuads
	@text	Reserve UV quads.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number nUVQuads
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_reserveUVQuads ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UN" )

	u32 total = state.GetValue < u32 >( 2, 0 );
	self->ReserveUVQuads ( total );

	return 0;
}

//----------------------------------------------------------------//
/**	@lua	setList
	@text	Initializes quad pair list at index. A list starts at the index
			of a pair and then continues sequentially for n pairs after. So
			a list with base 3 and a run of 4 would display pair 3, 4, 5,
			and 6.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number idx
	@in		number basePairID	The base pair of the list.
	@in		number totalPairs	The run of the list - total pairs to display (including base).
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_setList ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UNNN" )

	u32 idx = state.GetValue < u32 >( 2, 1 ) - 1;
	u32 basePairID = state.GetValue < u32 >( 3, 1 ) - 1;
	u32 totalPairs = state.GetValue < u32 >( 4, 0 );

	self->SetList ( idx, basePairID, totalPairs );

	return 0;
}

//----------------------------------------------------------------//
/**	@lua	setPair
	@text	Associates a quad with its UV coordinates.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number idx
	@in		number uvQuadID
	@in		number quadID
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_setPair ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UNNN" )

	u32 idx = state.GetValue < u32 >( 2, 1 ) - 1;
	if ( !MOAILogMessages::CheckIndexPlusOne ( idx, self->mPairs.Size (), L )) {
		return 0;
	}
	
	u32 uvQuadID = state.GetValue < u32 >( 3, 1 ) - 1;
	if ( !MOAILogMessages::CheckIndexPlusOne ( uvQuadID, self->mUVQuads.Size (), L )) {
		return 0;
	}
	
	u32 quadID = state.GetValue < u32 >( 4, 1 ) - 1;
	if ( !MOAILogMessages::CheckIndexPlusOne ( quadID, self->mQuads.Size (), L )) {
		return 0;
	}
	
	u32 maskBit = state.GetValue < u32 >( 5, 0 );
	self->SetPair ( idx, uvQuadID, quadID, maskBit );

	return 0;
}

//----------------------------------------------------------------//
/**	@lua	setQuad
	@text	Set model space quad given a valid deck index. Vertex order is
			clockwise from upper left (xMin, yMax)
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number idx	Index of the quad.
	@in		number x0
	@in		number y0
	@in		number x1
	@in		number y1
	@in		number x2
	@in		number y2
	@in		number x3
	@in		number y3
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_setQuad ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UNNNNNNNNN" )

	u32 idx = state.GetValue < u32 >( 2, 1 ) - 1;
	if ( MOAILogMessages::CheckIndexPlusOne ( idx, self->mQuads.Size (), L )) {
	
		ZLQuad quad;
		
		quad.mV [ 0 ].mX = state.GetValue < float >( 3, 0.0f );
		quad.mV [ 0 ].mY = state.GetValue < float >( 4, 0.0f );
		quad.mV [ 1 ].mX = state.GetValue < float >( 5, 0.0f );
		quad.mV [ 1 ].mY = state.GetValue < float >( 6, 0.0f );
		quad.mV [ 2 ].mX = state.GetValue < float >( 7, 0.0f );
		quad.mV [ 2 ].mY = state.GetValue < float >( 8, 0.0f );
		quad.mV [ 3 ].mX = state.GetValue < float >( 9, 0.0f );
		quad.mV [ 3 ].mY = state.GetValue < float >( 10, 0.0f );

		self->SetQuad ( idx, quad );
		self->SetBoundsDirty ();
	}
	return 0;
}

//----------------------------------------------------------------//
/**	@lua	setRect
	@text	Set model space quad given a valid deck index and a rect.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number idx	Index of the quad.
	@in		number xMin
	@in		number yMin
	@in		number xMax
	@in		number yMax
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_setRect ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UNNNNN" )

	u32 idx = state.GetValue < u32 >( 2, 1 ) - 1;
	if ( MOAILogMessages::CheckIndexPlusOne ( idx, self->mQuads.Size (), L )) {
	
		ZLRect rect;
		
		rect.mXMin = state.GetValue < float >( 3, 0.0f );
		rect.mYMin = state.GetValue < float >( 4, 0.0f );
		rect.mXMax = state.GetValue < float >( 5, 0.0f );
		rect.mYMax = state.GetValue < float >( 6, 0.0f );

		self->SetRect ( idx, rect );
		self->SetBoundsDirty ();
	}
	return 0;
}

//----------------------------------------------------------------//
/**	@lua	setUVQuad
	@text	Set UV space quad given a valid deck index. Vertex order is
			clockwise from upper left (xMin, yMax)
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number idx	Index of the quad.
	@in		number x0
	@in		number y0
	@in		number x1
	@in		number y1
	@in		number x2
	@in		number y2
	@in		number x3
	@in		number y3
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_setUVQuad ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UNNNNNNNNN" )

	u32 idx = state.GetValue < u32 >( 2, 1 ) - 1;
	if ( MOAILogMessages::CheckIndexPlusOne ( idx, self->mUVQuads.Size (), L )) {
	
		ZLQuad quad;
		
		quad.mV [ 0 ].mX = state.GetValue < float >( 3, 0.0f );
		quad.mV [ 0 ].mY = state.GetValue < float >( 4, 0.0f );
		quad.mV [ 1 ].mX = state.GetValue < float >( 5, 0.0f );
		quad.mV [ 1 ].mY = state.GetValue < float >( 6, 0.0f );
		quad.mV [ 2 ].mX = state.GetValue < float >( 7, 0.0f );
		quad.mV [ 2 ].mY = state.GetValue < float >( 8, 0.0f );
		quad.mV [ 3 ].mX = state.GetValue < float >( 9, 0.0f );
		quad.mV [ 3 ].mY = state.GetValue < float >( 10, 0.0f );

		self->SetUVQuad ( idx, quad );
	}
	return 0;
}

//----------------------------------------------------------------//
/**	@lua	setUVRect
	@text	Set UV space quad given a valid deck index and a rect.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		number idx	Index of the quad.
	@in		number xMin
	@in		number yMin
	@in		number xMax
	@in		number yMax
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_setUVRect ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UNNNNN" )

	u32 idx = state.GetValue < u32 >( 2, 1 ) - 1;
	if ( MOAILogMessages::CheckIndexPlusOne ( idx, self->mUVQuads.Size (), L )) {
	
		ZLRect rect;
		
		rect.mXMin = state.GetValue < float >( 3, 0.0f );
		rect.mYMin = state.GetValue < float >( 4, 0.0f );
		rect.mXMax = state.GetValue < float >( 5, 0.0f );
		rect.mYMax = state.GetValue < float >( 6, 0.0f );

		self->SetUVRect ( idx, rect );
	}
	return 0;
}


int MOAIGfxMaskedQuadListDeck2D::_setZOffsetUnit ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UN" )
	float offsetUnit = state.GetValue < float >( 2, 0.01f );
	self->mZOffsetUnit = offsetUnit;
	return 0;
}

//----------------------------------------------------------------//
/**	@lua	transform
	@text	Apply the given MOAITransform to all the vertices in the deck.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		MOAITransform transform
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_transform ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UU" )
	
	MOAITransform* transform = state.GetLuaObject < MOAITransform >( 2, true );
	if ( transform ) {
		transform->ForceUpdate ();
		self->Transform ( transform->GetLocalToWorldMtx ());
		self->SetBoundsDirty ();
	}
	return 0;
}

//----------------------------------------------------------------//
/**	@lua	transformUV
	@text	Apply the given MOAITransform to all the uv coordinates in the deck.
	
	@in		MOAIGfxMaskedQuadListDeck2D self
	@in		MOAITransform transform
	@out	nil
*/
int MOAIGfxMaskedQuadListDeck2D::_transformUV ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2D, "UU" )
	
	MOAITransform* transform = state.GetLuaObject < MOAITransform >( 2, true );
	if ( transform ) {
		transform->ForceUpdate ();
		self->TransformUV ( transform->GetLocalToWorldMtx ());
	}
	return 0;
}

//================================================================//
// MOAIGfxMaskedQuadListDeck2D
//================================================================//

//----------------------------------------------------------------//
ZLBox MOAIGfxMaskedQuadListDeck2D::ComputeMaxBounds () {

	ZLRect rect;
	rect.Init ( 0.0f, 0.0f, 0.0f, 0.0f );

	u32 size = this->mQuads.Size ();
	for ( u32 i = 0; i < size; ++i ) {
		rect.Grow ( this->mQuads [ i ].GetBounds ());
	}
	
	ZLBox bounds;
	bounds.Init ( rect.mXMin, rect.mYMax, rect.mXMax, rect.mYMin, 0.0f, 0.0f );	
	return bounds;
}

//----------------------------------------------------------------//
bool MOAIGfxMaskedQuadListDeck2D::Contains ( u32 idx, MOAIDeckRemapper* remapper, const ZLVec2D& vec ) {
	
	u32 size = this->mSprites.Size ();
	if ( size ) {
		
		idx = remapper ? remapper->Remap ( idx ) : idx;
		idx = ( idx - 1 ) % size;
		USMSprite& brush = this->mSprites [ idx ];
		
		for ( u32 i = 0; i < brush.mTotalPairs; ++i ) {
			USMSpritePair& prim = this->mPairs [ brush.mBasePair + i ];
			if ( this->mQuads [ prim.mQuadID ].Contains ( vec.mX, vec.mY )) {
				return true;
			} 
		}
	}
	return false;
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::DrawIndex ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	return this->DrawIndex( idx, xOff, yOff, zOff, xScl, yScl, zScl, 0 );
}

void MOAIGfxMaskedQuadListDeck2D::DrawIndex ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl, u64 mask ) {
	UNUSED ( zScl );

	u32 size = this->mSprites.Size ();
	if ( size ) {

		MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
		MOAIQuadBrush::BindVertexFormat ( gfxDevice );
		
		gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
		gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );
		
		idx = ( idx - 1 ) % size;

		USMSprite& sprite = this->mSprites [ idx ];
		MOAIQuadBrush glQuad;
		
		u32 base = sprite.mBasePair;
		u32 top = base + sprite.mTotalPairs;
		
		u32 totalSpritePairs = this->mPairs.Size ();
		
		for ( u32 i = base; i < top; ++i ) {
			
			USMSpritePair spritePair = this->mPairs [ i % totalSpritePairs ];
			u64 maskSprite = (u64)1 << spritePair.mMaskBit;
			// printf( "%llu, %llu, %d \n", maskSprite, mask,  spritePair.mMaskBit );
			if( (maskSprite & mask) != 0 ) continue;

			ZLQuad& uvQuad = this->mUVQuads [ spritePair.mUVQuadID ]; 
			ZLQuad& quad = this->mQuads [ spritePair.mQuadID ];
			glQuad.SetUVs ( uvQuad.mV [ 0 ], uvQuad.mV [ 1 ], uvQuad.mV [ 2 ], uvQuad.mV [ 3 ] );
			glQuad.SetVerts ( quad.mV [ 0 ], quad.mV [ 1 ], quad.mV [ 2 ], quad.mV [ 3 ]);
			glQuad.Draw ( xOff, yOff, zOff + this->mZOffsetUnit * (float)( i - base ), xScl, yScl );
		}
	}
}

//----------------------------------------------------------------//
ZLBox MOAIGfxMaskedQuadListDeck2D::GetItemBounds ( u32 idx ) {
	
	ZLBox bounds;

	u32 size = this->mSprites.Size ();
	if ( size ) {

		idx = ( idx - 1 ) % size;

		ZLRect rect;
		USMSprite& sprite = this->mSprites [ idx ];
		
		if ( sprite.mTotalPairs ) {
			
			USMSpritePair prim = this->mPairs [ sprite.mBasePair ];
			ZLQuad& baseQuad = this->mQuads [ prim.mQuadID ];
			
			rect = baseQuad.GetBounds ();
			
			for ( u32 i	 = 1; i < sprite.mTotalPairs; ++i ) {
				
				prim = this->mPairs [ sprite.mBasePair + i ];
				rect.Grow ( this->mQuads [ prim.mQuadID ].GetBounds ());
			}
			
			bounds.Init ( rect.mXMin, rect.mYMax, rect.mXMax, rect.mYMin, 0.0f, 0.0f );	
			return bounds;
		}
		
		
	}

	bounds.Init ( 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f );	
	return bounds;
}

//----------------------------------------------------------------//
MOAIGfxMaskedQuadListDeck2D::MOAIGfxMaskedQuadListDeck2D () {
	
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIDeck )
	RTTI_END

	this->mZOffsetUnit = 0.01f;
	
	// this->SetContentMask ( MOAIProp::CAN_DRAW );
}

//----------------------------------------------------------------//
MOAIGfxMaskedQuadListDeck2D::~MOAIGfxMaskedQuadListDeck2D () {

	this->mTexture.Set ( *this, 0 );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::RegisterLuaClass ( MOAILuaState& state ) {
	
	MOAIDeck::RegisterLuaClass ( state );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::RegisterLuaFuncs ( MOAILuaState& state ) {

	MOAIDeck::RegisterLuaFuncs ( state );

	luaL_Reg regTable [] = {
		{ "reserveLists",		  _reserveLists   },
		{ "reservePairs",		  _reservePairs   },
		{ "reserveQuads",		  _reserveQuads   },
		{ "reserveUVQuads",		_reserveUVQuads },
		{ "setList",			    _setList        },
		{ "setPair",			    _setPair        },
		{ "setQuad",			    _setQuad        },
		{ "setRect",			    _setRect        },
		{ "setUVQuad",			  _setUVQuad      },
		{ "setUVRect",			  _setUVRect      },
		{ "setZOffsetUnit",   _setZOffsetUnit },
		{ "transform",			  _transform      },
		{ "transformUV",		  _transformUV    },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::ReserveLists ( u32 total ) {

	this->mSprites.Init ( total );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::ReservePairs ( u32 total ) {

	this->mPairs.Init ( total );
	
	USMSpritePair zero;
	zero.mQuadID		= 0;
	zero.mUVQuadID		= 0;
	
	this->mPairs.Fill ( zero );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::ReserveQuads ( u32 total ) {

	this->mQuads.Init ( total );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::ReserveUVQuads ( u32 total ) {

	this->mUVQuads.Init ( total );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::SetList ( u32 idx, u32 basePairID, u32 totalPairs ) {

	if ( !this->mSprites.Size ()) return;
	if ( !this->mPairs.Size ()) return;
	
	USMSprite& sprite = this->mSprites [ idx % this->mSprites.Size ()];
	
	sprite.mBasePair = basePairID % this->mPairs.Size ();
	sprite.mTotalPairs = totalPairs;
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::SetPair ( u32 idx, u32 uvQuadID, u32 quadID, u32 maskBit ) {
	
	if ( !this->mPairs.Size ()) return;
	if ( !this->mUVQuads.Size ()) return;
	if ( !this->mQuads.Size ()) return;
	
	USMSpritePair& spritePair = this->mPairs [ idx % this->mPairs.Size ()];
	
	spritePair.mUVQuadID = uvQuadID % this->mUVQuads.Size ();
	spritePair.mQuadID = quadID % this->mQuads.Size ();
	spritePair.mMaskBit	= maskBit ;
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::SetQuad ( u32 idx, ZLQuad& quad ) {

	if ( idx > this->mQuads.Size ()) return;
	this->mQuads [ idx ] = quad;
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::SetRect ( u32 idx, ZLRect& rect ) {

	if ( idx > this->mQuads.Size ()) return;
	this->mQuads [ idx ].Init ( rect );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::SetUVQuad ( u32 idx, ZLQuad& quad ) {

	if ( idx > this->mUVQuads.Size ()) return;
	this->mUVQuads [ idx ] = quad;
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::SetUVRect ( u32 idx, ZLRect& rect ) {

	if ( idx > this->mUVQuads.Size ()) return;
	this->mUVQuads [ idx ].Init ( rect );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::Transform ( const ZLAffine3D& mtx ) {

	u32 total = this->mQuads.Size ();
	for ( u32 i = 0; i < total; ++i ) {
		this->mQuads [ i ].Transform ( mtx );
	}
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2D::TransformUV ( const ZLAffine3D& mtx ) {

	u32 total = this->mQuads.Size ();
	for ( u32 i = 0; i < total; ++i ) {
		this->mUVQuads [ i ].Transform ( mtx );
	}
}

//----------------------------------------------------------------//
//QuadList Instance
//----------------------------------------------------------------//

//----------------------------------------------------------------//
int MOAIGfxMaskedQuadListDeck2DInstance::_setSource ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2DInstance, "UU" )
	
	self->mSourceDeck.Set ( *self, state.GetLuaObject < MOAIGfxMaskedQuadListDeck2D >( 2, true ));
	
	return 0;
}


//----------------------------------------------------------------//
int MOAIGfxMaskedQuadListDeck2DInstance::_setMask ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGfxMaskedQuadListDeck2DInstance, "UNB" )
		
	u32 bit = state.GetValue < u32 > ( 2, 0 );
	bool v = state.GetValue < bool > ( 3, true );

	self->SetMask( bit, v );
	
	return 0;
}


//----------------------------------------------------------------//
MOAIGfxMaskedQuadListDeck2DInstance::MOAIGfxMaskedQuadListDeck2DInstance () :
	mMask ( 0 )
{
	
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIDeck )
	RTTI_END
	// this->SetContentMask ( MOAIProp::CAN_DRAW );

}

//----------------------------------------------------------------//
MOAIGfxMaskedQuadListDeck2DInstance::~MOAIGfxMaskedQuadListDeck2DInstance () {
	this->mTexture.Set( *this, 0 );
	this->mSourceDeck.Set( *this, 0 );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2DInstance::RegisterLuaClass ( MOAILuaState& state ) {
	
	MOAIDeck::RegisterLuaClass ( state );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2DInstance::RegisterLuaFuncs ( MOAILuaState& state ) {

	MOAIDeck::RegisterLuaFuncs ( state );

	luaL_Reg regTable [] = {
		{ "setMask",		_setMask },
		{ "setSource",		_setSource },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2DInstance::SetMask ( u32 bit, bool value ) {
	if( value ) {
		this->mMask |= (u64)1 << bit;
	} else {
		this->mMask &= ~((u64)1 << bit);
	}
	// printf( "%d, %llu\n", bit, this->mMask );
}

u64 MOAIGfxMaskedQuadListDeck2DInstance::GetMask () {
	return this->mMask;
}

//----------------------------------------------------------------//
bool MOAIGfxMaskedQuadListDeck2DInstance::Contains ( u32 idx, MOAIDeckRemapper* remapper, const ZLVec2D& vec ) {
	if( !this->mSourceDeck ) return false;
	return this->mSourceDeck->Contains( idx, remapper, vec );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2DInstance::DrawIndex ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	UNUSED ( zScl );
	if( !this->mSourceDeck ) return;
	return this->mSourceDeck->DrawIndex( idx, xOff, yOff, zOff, xScl, yScl, zScl, this->mMask );
}

//----------------------------------------------------------------//
ZLBox MOAIGfxMaskedQuadListDeck2DInstance::ComputeMaxBounds () {

	if( !this->mSourceDeck ) {
		ZLBox bounds;
		bounds.Init ( 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f );	
		return bounds;
	}
	return this->mSourceDeck->ComputeMaxBounds();
}

//----------------------------------------------------------------//
ZLBox MOAIGfxMaskedQuadListDeck2DInstance::GetItemBounds ( u32 idx ) {
	if( !this->mSourceDeck ) {
		ZLBox bounds;
		bounds.Init ( 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f );	
		return bounds;
	}
	return this->mSourceDeck->GetItemBounds( idx );
}

//----------------------------------------------------------------//
void MOAIGfxMaskedQuadListDeck2DInstance::GetGfxState ( MOAIDeckGfxState& gfxState ) {
	if( !this->mSourceDeck ) {
		return;
	} else {
		return this->mSourceDeck->GetGfxState( gfxState );
	}
}

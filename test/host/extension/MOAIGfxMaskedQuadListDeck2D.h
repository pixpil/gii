// Copyright (c) 2010-2011 Zipline Games, Inc. All Rights Reserved.
// http://getmoai.com

#ifndef	MOAIGfxMaskedQuadListDeck2D_H
#define	MOAIGfxMaskedQuadListDeck2D_H

#include <moai-sim/MOAIDeck.h>
#include <moai-sim/MOAIQuadBrush.h>

//================================================================//
// USMSpritePair
//================================================================//
class MOAIGfxMaskedQuadListDeck2DInstance;

class USMSpritePair {
private:

	friend class MOAIGfxMaskedQuadListDeck2D;

	u32		mUVQuadID;
	u32		mQuadID;
	u32		mMaskBit;
};

//================================================================//
// USMSprite
//================================================================//
class USMSprite {
private:

	friend class MOAIGfxMaskedQuadListDeck2D;

	u32		mBasePair;
	u32		mTotalPairs;
};

//================================================================//
// MOAIGfxMaskedQuadListDeck2D
//================================================================//
/**	@lua	MOAIGfxMaskedQuadListDeck2D
	@text	Deck of lists of textured quads. UV and model space quads are
			specified independently and associated via pairs. Pairs are referenced
			by lists sequentially. There may be multiple pairs with the same
			UV/model quad indices if geometry is used in multiple lists.
*/
class MOAIGfxMaskedQuadListDeck2D :
	public MOAIDeck {
private:
	friend class MOAIGfxMaskedQuadListDeck2DInstance;
	
	ZLLeanArray < ZLQuad >			mUVQuads;
	ZLLeanArray < ZLQuad >			mQuads;
	ZLLeanArray < USMSpritePair >	mPairs;
	ZLLeanArray < USMSprite >		mSprites;

	float  mZOffsetUnit;
	
	//----------------------------------------------------------------//
	static int	_reserveLists   ( lua_State* L );
	static int	_reservePairs   ( lua_State* L );
	static int	_reserveQuads   ( lua_State* L );
	static int	_reserveUVQuads ( lua_State* L );
	static int	_setList        ( lua_State* L );
	static int	_setPair        ( lua_State* L );
	static int	_setQuad        ( lua_State* L );
	static int	_setRect        ( lua_State* L );
	static int	_setUVQuad      ( lua_State* L );
	static int	_setUVRect      ( lua_State* L );
	static int	_setZOffsetUnit ( lua_State* L );
	static int	_transform      ( lua_State* L );
	static int	_transformUV    ( lua_State* L );

	//----------------------------------------------------------------//
	ZLBox			ComputeMaxBounds		();
	ZLBox			GetItemBounds			( u32 idx );

public:
	
	DECL_LUA_FACTORY ( MOAIGfxMaskedQuadListDeck2D )
	
	//----------------------------------------------------------------//
	bool			Contains				( u32 idx, MOAIDeckRemapper* remapper, const ZLVec2D& vec );
	void			DrawIndex				( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );
	void			DrawIndex				( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl, u64 mask );
					MOAIGfxMaskedQuadListDeck2D	();
					~MOAIGfxMaskedQuadListDeck2D	();
	void			RegisterLuaClass		( MOAILuaState& state );
	void			RegisterLuaFuncs		( MOAILuaState& state );
	void			ReserveLists			( u32 total );
	void			ReservePairs			( u32 total );
	void			ReserveQuads			( u32 total );
	void			ReserveUVQuads			( u32 total );
	void			SetList					( u32 idx, u32 basePairID, u32 totalPairs );
	void			SetPair					( u32 idx, u32 uvRectID, u32 screenRectID, u32 maskBit );
	void			SetQuad					( u32 idx, ZLQuad& quad );
	void			SetRect					( u32 idx, ZLRect& rect );
	void			SetUVQuad				( u32 idx, ZLQuad& quad );
	void			SetUVRect				( u32 idx, ZLRect& rect );
	void			Transform				( const ZLAffine3D& mtx );
	void			TransformUV				( const ZLAffine3D& mtx );
};

//----------------------------------------------------------------//
class MOAIGfxMaskedQuadListDeck2DInstance:
	public MOAIDeck {
private:
		MOAILuaSharedPtr < MOAIGfxMaskedQuadListDeck2D > mSourceDeck;
		static int	_setSource				( lua_State* L );
		static int	_setMask				( lua_State* L );
		u64 mMask;

			//----------------------------------------------------------------//
		ZLBox			ComputeMaxBounds		();
		ZLBox			GetItemBounds			( u32 idx );

public:
	
	DECL_LUA_FACTORY ( MOAIGfxMaskedQuadListDeck2DInstance )

	void			SetMask				( u32 bit, bool value );
	u64			GetMask				();

	bool			Contains				( u32 idx, MOAIDeckRemapper* remapper, const ZLVec2D& vec );
	void			DrawIndex				( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );
	MOAIGfxMaskedQuadListDeck2DInstance	();
	~MOAIGfxMaskedQuadListDeck2DInstance	();

	void			RegisterLuaClass		( MOAILuaState& state );
	void			RegisterLuaFuncs		( MOAILuaState& state );
	
	virtual void			GetGfxState				( MOAIDeckGfxState& gfxState );
};

#endif

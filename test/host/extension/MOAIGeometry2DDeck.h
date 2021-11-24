#ifndef MOAIGEOMETRY2DDECK_H
#define MOAIGEOMETRY2DDECK_H

#include <moai-sim/headers.h>


//----------------------------------------------------------------//
class MOAIGeometry2DDeckPrim {
public:
	ZLColorVec mColor;
	void SetColor ( float r, float g, float b, float a );
	virtual ZLBox GetBounds ();
	virtual void Draw       ( float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {};
	virtual bool Inside     ( ZLVec3D vec, float pad );
	MOAIGeometry2DDeckPrim () {};
};


//----------------------------------------------------------------//
class MOAIGeometry2DDeckPrimRect :
	public MOAIGeometry2DDeckPrim {
public:
	ZLRect mRect;
	bool   mFilled;

	MOAIGeometry2DDeckPrimRect ( float x0, float y0, float x1, float y1, bool filled = false ) {
		this->mRect.Init( x0, y0, x1, y1 );
		this->mFilled = filled;
	}

	void Draw ( float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );
	ZLBox GetBounds ();
};


//----------------------------------------------------------------//
class MOAIGeometry2DDeckPrimCircle :
	public MOAIGeometry2DDeckPrim {
public:
	ZLVec2D mOrigin;
	float   mRadius;
	bool    mFilled;

	MOAIGeometry2DDeckPrimCircle ( float x, float y, float radius, bool filled = false ) {
		this->mOrigin.Init( x, y );
		this->mRadius = radius;
		this->mFilled = filled;
	}

	void Draw ( float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );
	ZLBox GetBounds ();
	bool Inside ( ZLVec3D vec, float pad );
};




//================================================================//
// MOAIGeometry2DDeck
//================================================================//
/**	@lua MOAIGeometry2DDeck
	@text Scriptable deck object.
*/
class MOAIGeometry2DDeck :
	public MOAIDeck {
private:

	ZLRect				mRect;
	ZLLeanArray < MOAIGeometry2DDeckPrim* > mPrims;
	//----------------------------------------------------------------//
	static int    _reserve             ( lua_State* L );
	static int    _setCircleItem       ( lua_State* L );
	static int    _setFilledCircleItem ( lua_State* L );
	static int    _setFilledRectItem   ( lua_State* L );
	static int    _setRect             ( lua_State* L );
	static int    _setRectItem         ( lua_State* L );

	//----------------------------------------------------------------//
	ZLBox			ComputeMaxBounds		();
	ZLBox			GetItemBounds			( u32 idx );

public:
	
	DECL_LUA_FACTORY ( MOAIGeometry2DDeck )
	
	//----------------------------------------------------------------//
	bool			Inside					( u32 idx, ZLVec3D vec, float pad );
	void			DrawIndex				( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );
	void			Reserve					( u32 size );
	void			Clear						();
	void			SetGeometry			( u32 idx, MOAIGeometry2DDeckPrim* prim );

					MOAIGeometry2DDeck			();
					~MOAIGeometry2DDeck			();
	void			RegisterLuaClass		( MOAILuaState& state );
	void			RegisterLuaFuncs		( MOAILuaState& state );
};

#endif


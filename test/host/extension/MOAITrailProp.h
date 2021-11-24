#ifndef MOAI_TRAIL_PROP_H
#define MOAI_TRAIL_PROP_H
#include <moai-core/pch.h>
#include <moai-sim/pch.h>
#include <moai-core/MOAILogMessages.h>

#include <moai-sim/MOAIGfxDevice.h>
#include <moai-sim/MOAIDeck.h>
#include <moai-sim/MOAIGraphicsProp.h>
#include <moai-sim/MOAIAction.h>
#include <moai-sim/MOAIQuadBrush.h>

//----------------------------------------------------------------//
class MOAITrailDeckSpan 
{
public:
	ZLVec2D mP1;
	ZLVec2D mP2;
	float   mTime;
};

class MOAITrailDeck :
	public MOAIDeck,
	public MOAIAction
{
private:
	static int _init         ( lua_State* L );
	static int _setParams    ( lua_State* L );
	static int _setUVRect    ( lua_State* L );
	static int _clear        ( lua_State* L );
	static int _push         ( lua_State* L );
	static int _pop          ( lua_State* L );

	ZLLeanArray < MOAITrailDeckSpan >	mSpans;
	u32     mHeadId;
	u32     mTailId;
	u32     mTotal;
	u32     mSmoothSteps;
	u32     mCPCount;
	float   mPrevCPTime;
	float   mCurrentTime;
	float   mShrinkDelay;

	ZLRect  mUVs;

	ZLVec2D mCP1[4];
	ZLVec2D mCP2[4];

	ZLBox   ComputeMaxBounds  ();
	ZLBox   GetItemBounds     ( u32 idx );


	void    OnUpdate ( double step );

	int     WrapId( int id ) {	return id % this->mTotal;	};
	// void    UpdateQuadsUVs ();

public:

	bool    IsDone              ();

	void    DrawIndex           ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );
	void    PushCP              ( ZLVec2D p1, ZLVec2D p2 );
	void    PushHeadSpan        ( ZLVec2D p1, ZLVec2D p2, float t );
	void    PopTailSpan         ();
	void    Clear               ();

	DECL_LUA_FACTORY ( MOAITrailDeck )
	
	MOAITrailDeck	 ();
	~MOAITrailDeck ();
	
	void    RegisterLuaClass   ( MOAILuaState& state );
	void    RegisterLuaFuncs   ( MOAILuaState& state );

};


//----------------------------------------------------------------//
class MOAITrailProp :
	public MOAIGraphicsProp,
	public MOAIAction
{
private:

	static int _setParams    ( lua_State* L );

	float mLength;
	float mStep;

	void  OnUpdate ( float step );

public:

	void  Draw     ( int subPrimID );

	DECL_LUA_FACTORY ( MOAITrailProp )

	MOAITrailProp  ();
	~MOAITrailProp ();

	void  RegisterLuaClass ( MOAILuaState& state );
	void  RegisterLuaFuncs ( MOAILuaState& state );

};

#endif

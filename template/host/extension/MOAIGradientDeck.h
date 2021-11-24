#ifndef	MOAIGRADIENTDECK_H
#define	MOAIGRADIENTDECK_H

#include <moai-core/headers.h>
#include <moai-sim/headers.h>

#include <spine/spine.h>
#include <spine/extension.h>

//----------------------------------------------------------------//
typedef struct _GradientSpan {
	float          pos;
	u32            color;
	_GradientSpan* next;
} _GradientSpan;

//----------------------------------------------------------------//
class MOAIGradientDeck:
	public MOAIDeck
{
private:
	ZLRect mRect;
	//----------------------------------------------------------------//
	ZLBox			ComputeMaxBounds		();
	ZLBox			GetItemBounds			( u32 idx );

	static int _setRect      ( lua_State* L );
	static int _setSpan      ( lua_State* L );
	static int _setDirection ( lua_State* L );

	_GradientSpan *mHead;
	u32  mSpanCount;
	u32  mDirection;

	void  setSpan( float pos, float r, float g, float b, float a );


public:
	DECL_LUA_FACTORY ( MOAIGradientDeck )

	void			DrawIndex				( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );

	MOAIGradientDeck  ();
	~MOAIGradientDeck ();
	
	static const u32 DIRECTION_VERITICAL = 0;
	static const u32 DIRECTION_HORIZONTAL = 1;

	void			RegisterLuaClass		( MOAILuaState& state );
	void			RegisterLuaFuncs		( MOAILuaState& state );
	
};


#endif
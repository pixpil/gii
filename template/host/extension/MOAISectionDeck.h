#ifndef MOAISECTIONDECK_H
#define MOAISECTIONDECK_H
#include <moai-core/pch.h>
#include <moai-sim/pch.h>
#include <moai-core/MOAILogMessages.h>

#include <moai-sim/MOAIGfxDevice.h>
#include <moai-sim/MOAIDeck.h>
#include <moai-sim/MOAIGraphicsProp.h>
#include <moai-sim/MOAIAction.h>
#include <moai-sim/MOAIQuadBrush.h>	

class MOAISectionDeck:
	public MOAIDeck,
	public virtual MOAINode
{
private:
	static int _setRadius    ( lua_State* L );
	static int _setUVRect    ( lua_State* L );
	static int _setSection   ( lua_State* L );
	static int _seekAngle0   ( lua_State* L );
	static int _seekAngle1   ( lua_State* L );

	float mStepSize;
	float mRadius;
	float mLength;
	float mAngle0, mAngle1;
	ZLRect  mUVs;

	ZLBox   ComputeMaxBounds  ();
	ZLBox   GetItemBounds     ( u32 idx );

public:
	DECL_LUA_FACTORY ( MOAISectionDeck )
	DECL_ATTR_HELPER ( MOAISectionDeck )
	
	enum {
		ATTR_ANGLE0,
		ATTR_ANGLE1,		
		TOTAL_ATTR,
	};
	
	bool    ApplyAttrOp  ( u32 attrID, MOAIAttrOp& attrOp, u32 op );

	void    SetRadius    ( float radius, float length );
	void    SetSection   ( float angle0, float angle1, float stepSize );
	void    DrawIndex    ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl );

	
	void    RegisterLuaClass   ( MOAILuaState& state );
	void    RegisterLuaFuncs   ( MOAILuaState& state );

	MOAISectionDeck();
	~MOAISectionDeck();
};
#endif

#ifndef MOCKPROP_H
#define MOCKPROP_H

#include "moai-core/headers.h"
#include "moai-sim/headers.h"

class MOCKProp :
	public MOAIGraphicsProp
{
private:
	
	static int _setWorldLoc ( lua_State* L );

public:
	
	bool ApplyAttrOp ( u32 attrID, MOAIAttrOp& attrOp, u32 op );

	MOAITransformBase* FindParentTransform ();
	void SetWorldLoc ( const ZLVec3D& loc );

	DECL_LUA_FACTORY ( MOCKProp )

	MOCKProp();
	~MOCKProp();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};


#endif
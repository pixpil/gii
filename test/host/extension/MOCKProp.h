#ifndef MOCKPROP_H
#define MOCKPROP_H

#include "moai-core/headers.h"
#include "moai-sim/headers.h"

class MOCKProp :
	public MOAIGraphicsProp
{
private:
	
	static int _setWorldLoc ( lua_State* L );
	static int _setWorldRot ( lua_State* L );

public:
	DECL_LUA_FACTORY ( MOCKProp )
	DECL_ATTR_HELPER ( MOCKProp )
	
	enum {
		SYNC_WORLD_LOC,
		SYNC_WORLD_LOC_2D,
		TOTAL_ATTR
	};
	
	bool ApplyAttrOp ( u32 attrID, MOAIAttrOp& attrOp, u32 op );
	
	void OnDepNodeUpdate () ;
	MOAITransformBase* FindParentTransform ();
	void SetWorldLoc ( const ZLVec3D& loc );
	void SetWorldRot ( float rot );
	void SetWorldTransform2D( const ZLAffine3D& mtx );

	//----------------------------------------------------------------//
	MOCKProp();
	~MOCKProp();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};


#endif
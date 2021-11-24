#ifndef EWPROPRENDERTRANSFORM_H
#define EWPROPRENDERTRANSFORM_H

#include "moai-sim/headers.h"
class EWPropRenderTransform :
	public MOAIGraphicsProp
{
private:
	static int _setLogicTransform ( lua_State* L );
	static int _setRoundStep      ( lua_State* L );
	static int _setSyncRot        ( lua_State* L );
	static int _setFloorViewMode  ( lua_State* L );

public:
	bool mFloorViewMode;
	bool mFlagSyncRot;
	float mRoundStep;
	MOAILuaSharedPtr < MOAITransformBase > mLogicTransform;

	DECL_LUA_FACTORY ( EWPropRenderTransform )

	virtual void			BuildLocalToWorldMtx		( ZLAffine3D& localToWorldMtx );
	
	EWPropRenderTransform();
	~EWPropRenderTransform();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif
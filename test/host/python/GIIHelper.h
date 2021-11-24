#ifndef	GIIHELPER_H
#define	GIIHELPER_H
#include <moai-core/pch.h>
#include <moai-core/MOAILogMessages.h>

#include <moai-sim/headers.h>
// #include <moai-sim/MOAIGfxResourceMgr.h>
// #include <moai-sim/MOAIGfxDevice.h>
// // #include <moai-sim/MOAIInputMgr.h>
// #include <moai-sim/MOAINodeMgr.h>
// #include <moai-sim/MOAISim.h>
// #include <moai-sim/MOAITransform.h>
// #include <moai-sim/MOAITransformBase.h>
// // #include <moaicore/MOAITextureBase.h>
// // #include <moaicore/MOAIDebugLines.h>
// #include <moai-sim/MOAIFrameBuffer.h>
// #include <moai-sim/MOAIProp.h>


class GIIHelper:
	public ZLContextClass < GIIHelper, MOAINode > 
{
private:
	
	//----------------------------------------------------------------//
	static int _stepSim             ( lua_State* L );
	static int _updateInput         ( lua_State* L );
	static int _setBufferSize       ( lua_State* L );
	static int _renderFrameBuffer   ( lua_State* L );
	static int _setVertexTransform  ( lua_State* L );
	static int _copyWorldTransform  ( lua_State* L );
	static int _setWorldLoc  ( lua_State* L );
	static int _forceGC             ( lua_State* L );
	
public:
	
	DECL_LUA_SINGLETON ( GIIHelper )

	//
	void stepSim( double step );
	void updateInput( double step );

	//----------------------------------------------------------------//
	GIIHelper();
	~GIIHelper();
	
	void			RegisterLuaClass	( MOAILuaState& state );
};

extern "C"{
	void registerGIIHelper();
}


#endif
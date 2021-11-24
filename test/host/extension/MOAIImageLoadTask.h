#ifndef MOAIIMAGELOADTASK_H
#define MOAIIMAGELOADTASK_H


#include "moai-util/pch.h"
#include "moai-util/MOAITask.h"
#include "moai-sim/MOAIImage.h"

//================================================================//
// MOAIImageLoadTask
//================================================================//
class MOAIImageLoadTask : 
	public MOAITask {
private:

	MOAILuaSharedPtr < MOAIImage >	mImage;
	STLString							mFilename;
	MOAILuaMemberRef			mOnFinish;
	u32                   mTransform;
	//----------------------------------------------------------------//
	void		Execute				();
	void		Publish				();

	static int _start ( lua_State *L );

public:

	DECL_LUA_FACTORY ( MOAIImageLoadTask )

	//----------------------------------------------------------------//
				MOAIImageLoadTask		();
				~MOAIImageLoadTask		();
	void		RegisterLuaClass	( MOAILuaState& state );
	void		RegisterLuaFuncs	( MOAILuaState& state );
};

#endif

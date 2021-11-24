// Copyright (c) 2010-2011 Zipline Games, Inc. All Rights Reserved.
// http://getmoai.com

#ifndef	MOAIVIEWPINTRANSFORM_H
#define	MOAIVIEWPINTRANSFORM_H

#include <moai-sim/MOAITransform.h>

class MOAILayer;

//================================================================//
// MOAIViewPinTransform
//================================================================//
/**	@name	MOAIViewPinTransform
	@text	2D transform for connecting transforms across layers. Useful for
			HUD overlay items and map pins.
*/
class MOAIViewPinTransform :
	public MOAITransform {
private:

	MOAILuaSharedPtr < MOAILayer > mSourceLayer;

	//----------------------------------------------------------------//
	static int		_init						( lua_State* L );

	//----------------------------------------------------------------//
	void			OnDepNodeUpdate				();

public:
	
	DECL_LUA_FACTORY ( MOAIViewPinTransform )
	
	//----------------------------------------------------------------//
					MOAIViewPinTransform				();
					~MOAIViewPinTransform			();
	void			RegisterLuaClass			( MOAILuaState& state );
	void			RegisterLuaFuncs			( MOAILuaState& state );
};

#endif

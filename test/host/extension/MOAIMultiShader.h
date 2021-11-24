// Copyright (c) 2010-2011 Zipline Games, Inc. All Rights Reserved.
// http://getmoai.com

#ifndef	MOAIMULTISHADER_H
#define	MOAIMULTISHADER_H

#include "moai-sim/pch.h"
#include "moai-sim/MOAIShader.h"

//================================================================//
// MOAIMultiShader
//================================================================//
// TODO: doxygen
class MOAIMultiShader :
	public virtual MOAIShader {
protected:
	
	ZLLeanArray < MOAIShader* >		mSubShaders;
	MOAIShader* mDefaultShader;

	//----------------------------------------------------------------//
	static int		_reserve					( lua_State* L );
	static int		_getSubShader			( lua_State* L );
	static int		_setSubShader			( lua_State* L );
	static int		_getDefaultShader	( lua_State* L );
	static int		_setDefaultShader	( lua_State* L );

public:


	GET ( MOAIShaderProgram*, Program, mProgram )

	//----------------------------------------------------------------//
	void								BindUniforms			( u32 passId );
	MOAIShaderProgram*	GetProgram				( u32 passId );

	inline MOAIShader*	GetSubShader			( u32 passId );

	DECL_LUA_FACTORY ( MOAIMultiShader )

	MOAIMultiShader				();
	~MOAIMultiShader				();

	void			RegisterLuaClass		( MOAILuaState& state );
	void			RegisterLuaFuncs		( MOAILuaState& state );


};

#endif

#include "MOAIMultiShader.h"


int MOAIMultiShader::_reserve ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIMultiShader, "U" )
	u32 size = state.GetValue < u32 >( 2, 0 );
	self->mSubShaders.Init ( size );
	for ( u32 idx = 0; idx < self->mSubShaders.Size (); ++idx ) {
		self->mSubShaders[ idx ] = 0;
	}
	return 0;
}

int MOAIMultiShader::_getSubShader ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIMultiShader, "UN" )
	u32 idx = state.GetValue < u32 >( 2, 0 );
	if ( idx < self->mSubShaders.Size() ) {
		if( self->mSubShaders[ idx ] ) {
			self->mSubShaders[ idx ]->PushLuaUserdata( state );
			return 1;
		}
	}
	return 0;
}


int MOAIMultiShader::_setSubShader ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIMultiShader, "UN" )
	u32 idx = state.GetValue < u32 >( 2, 1 ) - 1;
	MOAIShader* shader = state.GetLuaObject < MOAIShader >( 3, 0 );

	if ( idx < self->mSubShaders.Size ()) {
		self->mSubShaders[ idx ] = shader;
		self->LuaRelease ( self->mSubShaders[ idx ] );
		self->LuaRetain( shader );
	}
	return 0;
}


int MOAIMultiShader::_getDefaultShader ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIMultiShader, "UN" )
	if( self->mDefaultShader ) {
		self->mDefaultShader->PushLuaUserdata( state );
		return 1;
	}
	return 0;
}


int MOAIMultiShader::_setDefaultShader ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIMultiShader, "U" )
	MOAIShader* shader = state.GetLuaObject < MOAIShader >( 2, 0 );
	self->LuaRelease( self->mDefaultShader );
	self->mDefaultShader = shader;
	self->LuaRetain( shader );
	return 0;
}


//----------------------------------------------------------------//
MOAIMultiShader::MOAIMultiShader() :
	mDefaultShader ( NULL )
{
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIShader )
	RTTI_END
}

MOAIMultiShader::~MOAIMultiShader() {
	for ( u32 i = 0; i < this->mSubShaders.Size (); ++i ) {
		this->LuaRelease ( this->mSubShaders [ i ]);
	}
	this->mSubShaders.Clear ();
}

//----------------------------------------------------------------//
MOAIShader*	MOAIMultiShader::GetSubShader ( u32 passId ) {
	MOAIShader* shader = 0; 
	if ( passId < this->mSubShaders.Size() ) {
		shader = this->mSubShaders[ passId ];
		if( shader ) {
			return shader;
		}
	}
	return this->mDefaultShader;
}

//----------------------------------------------------------------//
void MOAIMultiShader::BindUniforms ( u32 passId ) {
	MOAIShader* shader = this->GetSubShader( passId );
	if ( shader ) {
		shader->BindUniforms( passId );
	}
}

MOAIShaderProgram*	MOAIMultiShader::GetProgram ( u32 passId ) {
	MOAIShader* shader = this->GetSubShader( passId );
	if ( shader ) {
		return shader->GetProgram( passId );
	} else {
		return NULL;
	}
}


//----------------------------------------------------------------//
void MOAIMultiShader::RegisterLuaClass ( MOAILuaState& state ) {

	MOAINode::RegisterLuaClass ( state );
}

//----------------------------------------------------------------//
void MOAIMultiShader::RegisterLuaFuncs ( MOAILuaState& state ) {

	MOAINode::RegisterLuaFuncs ( state );

	luaL_Reg regTable [] = {
		{ "reserve",          _reserve          },
		{ "setSubShader",     _setSubShader     },
		{ "getSubShader",     _getSubShader     },
		{ "setDefaultShader", _setDefaultShader },
		{ NULL, NULL }
	};
	luaL_register ( state, 0, regTable );
}


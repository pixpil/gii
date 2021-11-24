// Copyright (c) 2010-2011 Zipline Games, Inc. All Rights Reserved.
// http://getmoai.com

#include <moai-sim/pch.h>
#include <moai-sim/MOAILayer.h>
#include <MOAIViewPinTransform.h>

//================================================================//
// local
//================================================================//

//----------------------------------------------------------------//
/**	@name	init
	@text	Initialize the bridge transform (map coordinates in one layer onto
			another; useful for rendering screen space objects tied to world
			space coordinates - map pins, for example).
	
	@in		MOAIViewPinTransform self
	@in		MOAITransformBase sourceTransform
	@in		MOAILayer sourceLayer
	@out	nil
*/
int MOAIViewPinTransform::_init ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIViewPinTransform, "UU" );
	
	MOAILayer* sourceLayer = state.GetLuaObject < MOAILayer >( 2, true );
	if ( !sourceLayer ) return 0;
	
	self->SetDependentMember ( self->mSourceLayer, sourceLayer );
	
	return 0;
}

//================================================================//
// MOAIViewPinTransform
//================================================================//

//----------------------------------------------------------------//
MOAIViewPinTransform::MOAIViewPinTransform () {
	
	RTTI_SINGLE ( MOAITransform )
}

//----------------------------------------------------------------//
MOAIViewPinTransform::~MOAIViewPinTransform () {

	this->mSourceLayer.Set ( *this, 0 );
}

//----------------------------------------------------------------//
void MOAIViewPinTransform::OnDepNodeUpdate () {
	
	MOAITransform::OnDepNodeUpdate ();
	
	if ( !this->mSourceLayer ) return;
	
	ZLVec3D loc = this->mLocalToWorldMtx.GetTranslation ();
	
	ZLMatrix4x4 mtx;
	
	this->mSourceLayer->GetWorldToWndMtx ().Project ( loc );
	
	this->mLocalToWorldMtx.Translate ( loc.mX, loc.mY, 0.0f );
	this->mWorldToLocalMtx.Translate ( -loc.mX, -loc.mY, 0.0f );
}

//----------------------------------------------------------------//
void MOAIViewPinTransform::RegisterLuaClass ( MOAILuaState& state ) {
	MOAITransform::RegisterLuaClass ( state );
}

//----------------------------------------------------------------//
void MOAIViewPinTransform::RegisterLuaFuncs ( MOAILuaState& state ) {
	
	MOAITransform::RegisterLuaFuncs ( state );
	
	luaL_Reg regTable [] = {
		{ "init",				_init },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}


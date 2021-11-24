#include "MOAISectionDeck.h"
#include <moai-sim/MOAISim.h>
#include <moai-sim/MOAIVertexFormatMgr.h>

//----------------------------------------------------------------//
int MOAISectionDeck::_setRadius ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISectionDeck, "UN" )	
	float radius = state.GetValue< float >( 2, 100.0f );
	float length = state.GetValue< float >( 3, radius );
	self->SetRadius( radius, length );
	return 0;
}

//----------------------------------------------------------------//
int MOAISectionDeck::_setSection ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISectionDeck, "UN" )	
	float angle0 = state.GetValue< float >( 2, 0.0f );
	float angle1 = state.GetValue< float >( 3, 0.0f );
	float step   = state.GetValue< float >( 4, 10.0f );
	self->SetSection( angle0, angle1, step );
	return 0;
}

//----------------------------------------------------------------//
int MOAISectionDeck::_setUVRect ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISectionDeck, "UNNNN" )	
	float u0   = state.GetValue< float >( 2, 0.0f );
	float v0   = state.GetValue< float >( 3, 0.0f );
	float u1   = state.GetValue< float >( 4, 1.0f );
	float v1   = state.GetValue< float >( 5, 1.0f );
	self->mUVs.Init( u0, v0, u1, v1 );
	return 0;
}

//----------------------------------------------------------------//
int MOAISectionDeck::_seekAngle0 ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAISectionDeck, "U" )

	float delay		= state.GetValue < float >( 3, 0.0f );
	
	if ( delay > 0.0f ) {

		u32 mode = state.GetValue < u32 >( 4, ZLInterpolate::kSmooth );		
		
		MOAIEaseDriver* action = new MOAIEaseDriver ();
		
		action->ParseForSeek ( state, 2, self, 1, mode,
			MOAISectionDeckAttr::Pack ( ATTR_ANGLE0 ), self->mAngle0, 0.0f
		);
		
		action->SetSpan ( delay );

		action->Start ( MOAISim::Get ().GetActionMgr (), false );
		action->PushLuaUserdata ( state );
		return 1;
	}
	return 0;
}

//----------------------------------------------------------------//
int MOAISectionDeck::_seekAngle1 ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAISectionDeck, "U" )

	float delay		= state.GetValue < float >( 3, 0.0f );

		if ( delay > 0.0f ) {

		u32 mode = state.GetValue < u32 >( 4, ZLInterpolate::kSmooth );		
		
		MOAIEaseDriver* action = new MOAIEaseDriver ();
		
		action->ParseForSeek ( state, 2, self, 1, mode,
			MOAISectionDeckAttr::Pack ( ATTR_ANGLE1 ), self->mAngle1, 0.0f
		);
		
		action->SetSpan ( delay );
		action->Start ( MOAISim::Get ().GetActionMgr (), false );
		action->PushLuaUserdata ( state );
		return 1;
	}
	return 0;
}


//----------------------------------------------------------------//
MOAISectionDeck::MOAISectionDeck() {
	mStepSize = 10.0f;
	mRadius = 100.0f;
	mLength = 50.0f;
	mAngle0 = 0.0f;
	mAngle1 = 90.0f;
	mUVs.Init( 0.0f, 0.0f, 1.0f, 1.0f );
	RTTI_BEGIN
		RTTI_EXTEND( MOAIDeck )
	RTTI_END
}

MOAISectionDeck::~MOAISectionDeck(){

}


void MOAISectionDeck::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIDeck   :: RegisterLuaClass( state );	
	MOAINode   :: RegisterLuaClass( state );

	state.SetField ( -1, "ATTR_ANGLE0", MOAISectionDeckAttr::Pack ( ATTR_ANGLE0 ));
	state.SetField ( -1, "ATTR_ANGLE1", MOAISectionDeckAttr::Pack ( ATTR_ANGLE1 ));
}

//----------------------------------------------------------------//
void MOAISectionDeck::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAIDeck   :: RegisterLuaFuncs( state );
	MOAINode   :: RegisterLuaFuncs( state );
	
	luaL_Reg regTable [] = {
		{ "setRadius",    _setRadius },
		{ "setSection",   _setSection },
		{ "setUVRect",    _setUVRect },
		{ "seekAngle0",   _seekAngle0 },
		{ "seekAngle1",   _seekAngle1 },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

bool MOAISectionDeck::ApplyAttrOp ( u32 attrID, MOAIAttrOp& attrOp, u32 op ) {

	if ( MOAISectionDeckAttr::Check ( attrID )) {
		attrID = UNPACK_ATTR ( attrID );
		
		if ( attrID == ATTR_ANGLE0 ) {
			this->mAngle0 = attrOp.Apply ( this->mAngle0, op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT );
			return true;
		} else if ( attrID == ATTR_ANGLE1 ) {
			this->mAngle1 = attrOp.Apply ( this->mAngle1, op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT );
			return true;
		}
	}
	return false;
}

ZLBox MOAISectionDeck::ComputeMaxBounds () {
	return this->GetItemBounds ( 0 );
}

ZLBox MOAISectionDeck::GetItemBounds ( u32 idx ) {
	UNUSED ( idx );
	ZLBox bounds;
	bounds.Init ( -50, 50, 50, -50, 0, 0 );//todo
	return bounds;
}

void MOAISectionDeck::SetRadius( float radius, float length ) {
	mRadius = radius;
	mLength = length;
}

void MOAISectionDeck::SetSection( float a0, float a1, float step ) {
	mAngle0 = a0;
	mAngle1 = a1;
	mStepSize = step;
}

void MOAISectionDeck::DrawIndex ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();

	gfxDevice.SetVertexPreset ( MOAIVertexFormatMgr::XYZWUVC );
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );
	gfxDevice.BeginPrim ( ZGL_PRIM_TRIANGLE_STRIP );

	int spans = ( int ) ( mAngle1 - mAngle0 ) / mStepSize;
	if( spans == 0 ) return;
	if( spans < 0 ) spans = -spans;
	float step = ( mAngle1 - mAngle0 ) / (float) spans;
	float vDiff = mUVs.mYMin - mUVs.mYMax;
	float r2    = mRadius;
	float r1    = mRadius - mLength;
	for( u32 i = 0; i <= spans; i++ ) {
		float angle = mAngle0 + step * (float) i;
		float k = ( float ) i / ( float ) spans;
		float vOff = k * vDiff;
		float c, s;
		float x, y;
		c = Cos( angle * D2R );
		s = Sin( angle * D2R );
		gfxDevice.WriteVtx ( c * r1 * xScl + xOff, s * r1 * yScl + yOff, zOff );
		gfxDevice.WriteUV( mUVs.mXMin, vOff + mUVs.mYMax );
		gfxDevice.WriteFinalColor4b ();
		gfxDevice.WriteVtx ( c * r2 * xScl + xOff, s * r2 * yScl + yOff, zOff );
		gfxDevice.WriteUV( mUVs.mXMax, vOff + mUVs.mYMax );
		gfxDevice.WriteFinalColor4b ();
	}
	gfxDevice.EndPrim();
}


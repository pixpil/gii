#include "MOAIGradientDeck.h"
#include <moai-sim/MOAIShaderMgr.h>


int MOAIGradientDeck::_setRect ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGradientDeck, "UNNNN" )
	
	float x0	= state.GetValue < float >( 2, 0.0f );
	float y0	= state.GetValue < float >( 3, 0.0f );
	float x1	= state.GetValue < float >( 4, 0.0f );
	float y1	= state.GetValue < float >( 5, 0.0f );
	
	self->mRect.Init( x0, y0, x1, y1 );
	self->SetBoundsDirty ();
	return 0;
}


int MOAIGradientDeck::_setSpan ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGradientDeck, "UN" )
	
	float pos	= state.GetValue < float >( 2, 0.0f );
	float r	  = state.GetValue < float >( 3, 1.0f );
	float g	  = state.GetValue < float >( 4, 1.0f );
	float b	  = state.GetValue < float >( 5, 1.0f );
	float a	  = state.GetValue < float >( 6, 1.0f );
	self->setSpan( pos, r,g,b,a );
	return 0;
}

int MOAIGradientDeck::_setDirection ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIGradientDeck, "UN" )
	self->mDirection = state.GetValue < u32 >( 2, 0 );
	return 0;
}

//----------------------------------------------------------------//
void  MOAIGradientDeck::setSpan( float pos, float r, float g, float b, float a ) {
	
	_GradientSpan* it = mHead;
	while( it ) {		
		if( it->pos == pos ) {
			it->color = ZLColor::PackRGBA( r,g,b,a );
			return;
		}
		if( it->pos > pos ) {
			it = NULL;
			break;
		}
		if( !it->next || it->next->pos > pos ) break;
		it = it -> next;
	}
	_GradientSpan* span = new _GradientSpan();
	span->pos = pos;
	span->color = ZLColor::PackRGBA( r,g,b,a );
	if( it ) {
		span->next = it->next;
		it->next = span;
	} else {
		span->next = mHead;	
		mHead = span;
	}
	mSpanCount++;
}

//----------------------------------------------------------------//
void MOAIGradientDeck::DrawIndex ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	UNUSED ( idx );
	UNUSED ( zScl );
	if( mSpanCount < 2 ) return;
	
	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
	gfxDevice.SetVertexPreset ( MOAIVertexFormatMgr::XYZWC );
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );

	gfxDevice.BeginPrim ( ZGL_PRIM_TRIANGLE_STRIP );
		_GradientSpan* it = mHead;
		if( mDirection == DIRECTION_VERITICAL ) {
			float ySize = mRect.mYMax - mRect.mYMin;
			while( it ) {
				//span0
				float y = ySize * it->pos;
				gfxDevice.WriteVtx ( mRect.mXMin * xScl + xOff, y * yScl + yOff, zOff );
				gfxDevice.Write < u32 >( it->color );			
				//span1
				gfxDevice.WriteVtx ( mRect.mXMax * xScl + xOff, y * yScl + yOff, zOff );
				gfxDevice.Write < u32 >( it->color );
				it = it->next;
			}
		}	else {
			float xSize = mRect.mXMax - mRect.mXMin;
			while( it ) {
				//span0
				float x = xSize * it->pos;
				gfxDevice.WriteVtx ( x * xScl + xOff, mRect.mYMin * yScl + yOff, zOff );
				gfxDevice.Write < u32 >( it->color );			
				//span1
				gfxDevice.WriteVtx ( x * xScl + xOff, mRect.mYMax * yScl + yOff, zOff );
				gfxDevice.Write < u32 >( it->color );
				it = it->next;
			}
		}
	gfxDevice.EndPrim ();
}

//----------------------------------------------------------------//
ZLBox MOAIGradientDeck::ComputeMaxBounds () {
	return this->GetItemBounds ( 0 );
}

//----------------------------------------------------------------//
ZLBox MOAIGradientDeck::GetItemBounds ( u32 idx ) {
	UNUSED ( idx );
	ZLBox bounds;
	bounds.Init ( mRect.mXMin, mRect.mYMax, mRect.mXMax, mRect.mYMin, 0.0f, 0.0f );	
	return bounds;
}

//----------------------------------------------------------------//
MOAIGradientDeck::MOAIGradientDeck ()
: mHead( NULL ), mSpanCount( 0 ), mDirection( DIRECTION_VERITICAL )
{

	RTTI_BEGIN
		RTTI_EXTEND ( MOAIDeck )
	RTTI_END
	
	this->mDefaultShaderID = MOAIShaderMgr::LINE_SHADER;
	// set up rects to draw a unit tile centered at the origin
	mRect.Init ( -0.5f, -0.5f, 0.5f, 0.5f );
}

//----------------------------------------------------------------//
MOAIGradientDeck::~MOAIGradientDeck () {
	this->mTexture.Set ( *this, 0 );
	//clear span
	_GradientSpan* it = mHead;
	while( it ) {
		_GradientSpan* next = it->next;
		delete it;
		it = next;
	}
}

//----------------------------------------------------------------//
void MOAIGradientDeck::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIDeck::RegisterLuaClass ( state );
	state.SetField ( -1, "DIRECTION_VERITICAL",  ( u32 )DIRECTION_VERITICAL  );
  state.SetField ( -1, "DIRECTION_HORIZONTAL", ( u32 )DIRECTION_HORIZONTAL );
}

void MOAIGradientDeck::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAIDeck::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "setRect",        _setRect },
		{ "setSpan",        _setSpan },
		{ "setDirection",   _setDirection },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}


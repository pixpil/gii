#include "MOAITileMesh.h"
#include <moai-sim/MOAIShaderMgr.h>

//----------------------------------------------------------------//
// TODO: doxygen
int MOAITileMesh::_reserveTiles ( lua_State* L ) {
	MOAI_LUA_SETUP( MOAITileMesh, "UN" )
	u32 count = state.GetValue < u32 >( 2, 0 );
	self->ReserveTiles ( count );
	return 0;
}
	
int MOAITileMesh::_setTile ( lua_State* L ) {
	MOAI_LUA_SETUP( MOAITileMesh, "UNNN" )
	u32 idx   = state.GetValue < u32 >( 2, 1 ) - 1;
	u32 start = state.GetValue < u32 >( 3, 0 );
	u32 count = state.GetValue < u32 >( 4, 0 );
	self->SetTile ( idx, start, count );
	return 0;
}

//----------------------------------------------------------------//
void MOAITileMesh::ReserveTiles ( u32 count ) {
	this->mMeshSpans.Init( count );
}

void MOAITileMesh::SetTile ( u32 idx, u32 start, u32 count ) {
	if ( idx >= this->mMeshSpans.Size() ) return;
	this->mMeshSpans[ idx ].Init( start, count );
}


//----------------------------------------------------------------//
void MOAITileMesh::PreDraw () {
	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
	
	this->mRetainedMtx.Init( gfxDevice.GetVertexTransform ( MOAIGfxDevice::VTX_WORLD_TRANSFORM ) );
	
	gfxDevice.Flush ();
	this->FinishInit ();
	MOAIGfxDevice::Get ().SetVertexFormat ();
	this->Bind ();
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_MODEL );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );
	gfxDevice.SetGfxState ( this->mTexture );
	
	gfxDevice.SetPenWidth ( this->mPenWidth );
	gfxDevice.SetPointSize ( this->mPointSize );
	
}
		

void MOAITileMesh::PostDraw () {
	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
	gfxDevice.SetVertexTransform( MOAIGfxDevice::VTX_WORLD_TRANSFORM, this->mRetainedMtx );
	this->Unbind ();
}

//----------------------------------------------------------------//
void MOAITileMesh::PreGridDraw () {
	this->mInsideGridDraw = true;
	this->PreDraw();
}

//----------------------------------------------------------------//
void MOAITileMesh::PostGridDraw () {
	this->mInsideGridDraw = false;
	this->PostDraw();
}

//----------------------------------------------------------------//
void MOAITileMesh::DrawIndex ( u32 idx, float xOff, float yOff, float zOff, float xScl, float yScl, float zScl ) {
	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
	if( !this->mInsideGridDraw ) {
		this->PreDraw();		
	}

	u32 offset = 0;
	u32 count = this->mTotalElements;
	
	if ( this->mMeshSpans.Size()>0 && idx <= this->mMeshSpans.Size() ) {
		offset = this->mMeshSpans[ idx - 1 ].mOffset;
		count  = this->mMeshSpans[ idx - 1 ].mCount;
	}
	ZLMatrix4x4 offsetMtx;
	offsetMtx.ScRoTr( xScl, yScl, zScl, 0.0f, 0.0f, 0.0f, xOff, yOff, zOff );
	ZLMatrix4x4 offsetedMtx;
	offsetedMtx.Multiply( this->mRetainedMtx, offsetMtx );
	gfxDevice.SetVertexTransform( MOAIGfxDevice::VTX_WORLD_TRANSFORM, offsetedMtx );
	gfxDevice.UpdateShaderGlobals ();


	if ( this->mIndexBuffer ) {
			if ( this->mIndexBuffer->Bind ()) {
				//TODO
				zglDrawElements ( this->mPrimType, this->mTotalElements, this->mIndexSizeInBytes == 2 ? ZGL_TYPE_UNSIGNED_SHORT : ZGL_TYPE_UNSIGNED_INT, 0 );
			}
		}
		else {
			zglDrawArrays ( this->mPrimType, offset, count );
		}

	if ( !this->mInsideGridDraw ) {
		this->PostDraw();
	}
	

}

//----------------------------------------------------------------//
MOAITileMesh::MOAITileMesh () {
	this->mInsideGridDraw = false;
	this->mTileCount      = 0;
	this->mMeshSpans.Init( 1 );
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIMesh )
	RTTI_END
}

//----------------------------------------------------------------//
MOAITileMesh::~MOAITileMesh () {
}

//----------------------------------------------------------------//
void MOAITileMesh::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIMesh::RegisterLuaClass ( state );
}

void MOAITileMesh::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAIMesh::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "reserveTiles",	_reserveTiles },
		{ "setTile",			_setTile },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}


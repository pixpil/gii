#include "MOAISpineSkeleton.h"

#ifndef SPINE_MESH_VERTEX_COUNT_MAX
#define SPINE_MESH_VERTEX_COUNT_MAX 200
#endif


//----------------------------------------------------------------//
//----------------------------------------------------------------//
//MOAISpineSkeletonBase
//----------------------------------------------------------------//
//----------------------------------------------------------------//

int MOAISpineSkeletonBase::_load ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "UU" )
	MOAISpineSkeletonData* data = state.GetLuaObject < MOAISpineSkeletonData >( 2, true );
	if ( !data ) return 0;
	float zscale = state.GetValue< float >( 3, 0.001 );
	bool  useAlphaBlend = state.GetValue< bool >( 4, false );
	self->Load( data, zscale, useAlphaBlend );
	state.Push( true );
	return 1;
}

int MOAISpineSkeletonBase::_unload ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "U" )
	self->Unload();
	return 0;
}

int MOAISpineSkeletonBase::_getSkeletonData ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "U" )
	if( self->mData ) {
		self->mData->PushLuaUserdata( state );
		return 1;
	}
	return 0;
}

int MOAISpineSkeletonBase::_getSlotBoneName ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "US" )
	if( !self->mSkeleton ) return 0;
	cc8* slotName = lua_tostring( L, 2 );
	Slot* slot = Skeleton_findSlot( self->mSkeleton, slotName );
	if( !slot ) return 0;
	lua_pushstring( L, slot->bone->data->name );
	return 1;
}

int MOAISpineSkeletonBase::_getBoneParentName ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "US" )
	if( !self->mSkeleton ) return 0;
	cc8* boneName = lua_tostring( L, 2 );
	Bone* bone = Skeleton_findBone( self->mSkeleton, boneName );
	if( !bone ) return 0;
	if( !bone->parent ) return 0;
	lua_pushstring( L, bone->parent->data->name );
	return 1;
}

int MOAISpineSkeletonBase::_setAttachment ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "US" )
	cc8* slotName = lua_tostring( L, 2 );
	int tt = lua_type( L, 3 );
	if( tt == LUA_TSTRING ) {
		cc8* attachmentName = lua_tostring( L, 3 );
		self->SetAttachment( slotName, attachmentName );
	} else if ( tt == LUA_TBOOLEAN && !lua_toboolean( L, 3 ) ) {
		self->SetAttachment( slotName, NULL );
	}
	return 0;
}

int MOAISpineSkeletonBase::_setSkin ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "US" )
	cc8* skinName = lua_tostring( L, 2 );
	self->SetSkin( skinName );
	return 0;
}


int MOAISpineSkeletonBase::_getBoneLoc ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "US" )
	cc8* boneName = lua_tostring( L, 2 );
	Bone* bone = Skeleton_findBone( self->mSkeleton, boneName );
	if( !bone ) return 0;
	state.Push( bone->x );
	state.Push( bone->y );
	return 2;
}

int MOAISpineSkeletonBase::_getBoneScl ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "US" )
	cc8* boneName = lua_tostring( L, 2 );
	Bone* bone = Skeleton_findBone( self->mSkeleton, boneName );
	if( !bone ) return 0;
	state.Push( bone->scaleX );
	state.Push( bone->scaleY );
	return 2;
}

int MOAISpineSkeletonBase::_getBoneRot ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "US" )
	cc8* boneName = lua_tostring( L, 2 );
	Bone* bone = Skeleton_findBone( self->mSkeleton, boneName );
	if( !bone ) return 0;
	state.Push( bone->rotation );
	return 1;
}

int MOAISpineSkeletonBase::_getBoneLength ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "US" )
	cc8* boneName = lua_tostring( L, 2 );
	Bone* bone = Skeleton_findBone( self->mSkeleton, boneName );
	if( !bone ) return 0;
	state.Push( bone->data->length );
	return 1;
}


int MOAISpineSkeletonBase::_setBoneLoc ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "USNN" )
	cc8* boneName = lua_tostring( L, 2 );
	Bone* bone = Skeleton_findBone( self->mSkeleton, boneName );
	if( !bone ) return 0;
	float x = state.GetValue < float > ( 3, 0 );
	float y = state.GetValue < float > ( 4, 0 );
	bone->x = x;
	bone->y = y;
	return 0;
}


int MOAISpineSkeletonBase::_setBoneScl ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "USNN" )
	cc8* boneName = lua_tostring( L, 2 );
	Bone* bone = Skeleton_findBone( self->mSkeleton, boneName );
	if( !bone ) return 0;
	float x = state.GetValue < float > ( 3, 0 );
	float y = state.GetValue < float > ( 4, 0 );
	bone->scaleX = x;
	bone->scaleY = y;
	return 0;
}


int MOAISpineSkeletonBase::_setBoneRot ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "USN" )
	cc8* boneName = lua_tostring( L, 2 );
	Bone* bone = Skeleton_findBone( self->mSkeleton, boneName );
	if( !bone ) return 0;
	float rotation = state.GetValue < float > ( 3, 0 );
	bone->rotation = rotation;
	return 0;
}

int MOAISpineSkeletonBase::_updateSpine ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "U" )
	self->UpdateSpine();
	return 0;
}

int MOAISpineSkeletonBase::_setToSetupPose ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "U" )
	Skeleton_setToSetupPose( self->mSkeleton );
	self->UpdateSpine();
	return 0;
}

int MOAISpineSkeletonBase::_setBonesToSetupPose ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "U" )
	Skeleton_setBonesToSetupPose( self->mSkeleton );
	self->UpdateSpine();
	return 0;
}

int MOAISpineSkeletonBase::_setSlotsToSetupPose ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonBase, "U" )
	Skeleton_setSlotsToSetupPose( self->mSkeleton );
	self->UpdateSpine();
	return 0;
}


//----------------------------------------------------------------//
//Lua Registration
//----------------------------------------------------------------//
void	MOAISpineSkeletonBase::RegisterLuaClass	( MOAILuaState& state ){
	UNUSED( state );
}

void	MOAISpineSkeletonBase::RegisterLuaFuncs	( MOAILuaState& state ){
	MOAIGraphicsProp::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "load",                  _load },
		{ "unload",                _unload },
		{ "getSkeletonData",       _getSkeletonData },		
		{ "updateSpine",           _updateSpine },
		{ "setSkin",               _setSkin },
		{ "setAttachment",         _setAttachment },
		{ "setToSetupPose",        _setToSetupPose },
		{ "setSlotsToSetupPose",   _setSlotsToSetupPose },
		{ "setBonesToSetupPose",   _setBonesToSetupPose },
		{ "setBoneRot",            _setBoneRot },
		{ "setBoneLoc",            _setBoneLoc },
		{ "setBoneScl",            _setBoneScl },
		{ "getBoneRot",            _getBoneRot },
		{ "getBoneLoc",            _getBoneLoc },
		{ "getBoneScl",            _getBoneScl },
		{ "getBoneLength",         _getBoneLength },
		{ "getBoneParentName",     _getBoneParentName },
		{ "getSlotBoneName",       _getSlotBoneName },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}


//----------------------------------------------------------------//
// Ctor, Dtor
//----------------------------------------------------------------//
MOAISpineSkeletonBase::MOAISpineSkeletonBase()
: mSkeleton( NULL )
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAIGraphicsProp )
	RTTI_END
}

MOAISpineSkeletonBase::~MOAISpineSkeletonBase() {
	//remove slots props
	// this->Unload();	
}


//----------------------------------------------------------------//
void	MOAISpineSkeletonBase::OnLoad( MOAISpineSkeletonData* data, float ZScale ) {
	UNUSED( data );
}

void	MOAISpineSkeletonBase::OnUnload	() {
}


//----------------------------------------------------------------//
void MOAISpineSkeletonBase::Load( MOAISpineSkeletonData* data, float ZScale, bool useAlphaBlend ) {
	mData.Set( *this, data );
	mSkeleton = Skeleton_create( mData->mData );
	Skeleton_setToSetupPose( mSkeleton );
	this->OnLoad( data, ZScale );
	UpdateSpine();
}

//----------------------------------------------------------------//
void MOAISpineSkeletonBase::Unload() {
	this->OnUnload();	
	if( mSkeleton ) {
		Skeleton_dispose( mSkeleton );
		mSkeleton = NULL;
	}
	mData.Set( *this, 0 );
}

//----------------------------------------------------------------//
void MOAISpineSkeletonBase::UpdateSpine() {	
}

//----------------------------------------------------------------//
void MOAISpineSkeletonBase::SetSkin( const char* skinName ) {
	if( !mSkeleton ) return;
	Skeleton_setSkinByName( mSkeleton, skinName );
	Skeleton_setSlotsToSetupPose( mSkeleton );
	UpdateSpine();
}

void MOAISpineSkeletonBase::SetAttachment( const char* slotName, const char* attachmentName ) {
	if( !mSkeleton ) return;
	Skeleton_setAttachment( mSkeleton, slotName, attachmentName );
}

void MOAISpineSkeletonBase::SetToSetupPose () {
	if( !mSkeleton ) return;
	Skeleton_setToSetupPose( mSkeleton );
}

void MOAISpineSkeletonBase::SetBonesToSetupPose () {
	if( !mSkeleton ) return;
	Skeleton_setBonesToSetupPose( mSkeleton );
}

void MOAISpineSkeletonBase::SetSlotsToSetupPose () {
	if( !mSkeleton ) return;
	Skeleton_setSlotsToSetupPose( mSkeleton );
}



//----------------------------------------------------------------//
//----------------------------------------------------------------//
//MOAISpineSkeletonSimple
//----------------------------------------------------------------//
//----------------------------------------------------------------//
MOAISpineSkeletonSimple::MOAISpineSkeletonSimple()
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAISpineSkeletonBase )
	RTTI_END
	mShader.Set( *this,
		&MOAIShaderMgr::Get ().GetShader ( MOAIShaderMgr::DECK2D_SHADER )
	);
}

MOAISpineSkeletonSimple::~MOAISpineSkeletonSimple() {
	this->Unload();
}

u32 MOAISpineSkeletonSimple::OnGetModelBounds  ( ZLBox& bounds ) {
	return BOUNDS_GLOBAL;
}

void MOAISpineSkeletonSimple::Draw ( int subPrimID, float lod ) {
	UNUSED ( subPrimID );

	if ( !this->IsVisible ( lod )) return;
	if ( !this->mSkeleton ) return;

	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();

	this->LoadGfxState ();
	this->LoadVertexTransform ();	
	
	gfxDevice.SetVertexPreset ( MOAIVertexFormatMgr::XYZWUVC );
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );
	
	Skeleton_updateWorldTransform( mSkeleton );

	for (int i = 0, n = this->mSkeleton->slotCount; i < n; i++) {
		Slot* slot = this->mSkeleton->drawOrder[i];
		if (!slot->attachment) continue;
		this->DrawSpineSlot( slot );
	}
}


static const int _quadTriangles[6] = {0, 1, 2, 2, 3, 0};
//----------------------------------------------------------------//
void MOAISpineSkeletonSimple::DrawSpineSlot ( Slot* slot ) {
	if( !slot->attachment ) return ;	
	
	float worldVertices[ SPINE_MESH_VERTEX_COUNT_MAX ];

	const float* uvs     = NULL;
	const int* triangles = NULL;
	int verticesCount    = 0;
	int trianglesCount   = 0;
	float r = 0, g = 0, b = 0, a = 0;
	MOAITexture* texture = NULL;
	
	if( slot->attachment->type == ATTACHMENT_REGION ) {
			RegionAttachment* attachment = (RegionAttachment*)slot->attachment;
			RegionAttachment_computeWorldVertices(
				attachment, slot->skeleton->x, slot->skeleton->y, slot->bone, worldVertices
			);
			texture        = (MOAITexture*) ((AtlasRegion*) attachment->rendererObject) ->rendererObject;
			uvs            = attachment->uvs;
			verticesCount  = 8;
			triangles      = _quadTriangles;
			trianglesCount = 6;
			r              = attachment->r;
			g              = attachment->g;
			b              = attachment->b;
			a              = attachment->a;

	} else if( slot->attachment->type == ATTACHMENT_MESH ) {
		MeshAttachment* attachment = (MeshAttachment*)slot->attachment;
		MeshAttachment_computeWorldVertices(
			attachment, slot->skeleton->x, slot->skeleton->y, slot, worldVertices
		);
		texture        = (MOAITexture*) ((AtlasRegion*) attachment->rendererObject) ->rendererObject;
		uvs            = attachment->uvs;
		verticesCount  = attachment->verticesCount;
		triangles      = attachment->triangles;
		trianglesCount = attachment->trianglesCount;
		r              = attachment->r;
		g              = attachment->g;
		b              = attachment->b;
		a              = attachment->a;

	} else if( slot->attachment->type == ATTACHMENT_SKINNED_MESH ) {
		SkinnedMeshAttachment* attachment = (SkinnedMeshAttachment*)slot->attachment;
		SkinnedMeshAttachment_computeWorldVertices(
			attachment, slot->skeleton->x, slot->skeleton->y, slot, worldVertices
		);
		texture        = (MOAITexture*) ((AtlasRegion*) attachment->rendererObject) ->rendererObject;
		uvs            = attachment->uvs;
		verticesCount  = attachment->uvsCount;
		triangles      = attachment->triangles;
		trianglesCount = attachment->trianglesCount;
		r              = attachment->r;
		g              = attachment->g;
		b              = attachment->b;
		a              = attachment->a;

	} else {
		return;
	}

	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();

	if( slot->data->additiveBlending ) {
		gfxDevice.SetBlendMode ( ZGL_BLEND_FACTOR_SRC_ALPHA, ZGL_BLEND_FACTOR_ONE );
	} else {
		gfxDevice.SetBlendMode ( ZGL_BLEND_FACTOR_SRC_ALPHA, ZGL_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA );
	}
	gfxDevice.SetPenColor( 
		slot->r * mColor.mR,
		slot->g * mColor.mG,
		slot->b * mColor.mB,
		slot->a * mColor.mA
	);
	gfxDevice.SetGfxState( texture );
	gfxDevice.SetPrimType( ZGL_PRIM_TRIANGLES );
	int c = trianglesCount / 3;
	for ( int j = 0; j < c; ++j ) {
		gfxDevice.BeginPrim ();
		for (int i = 0; i < 3; ++i) {
			int index = triangles[ i + j * 3 ] * 2;
			gfxDevice.WriteVtx ( worldVertices[ index ], worldVertices[ index+1 ], 0.0f );
			gfxDevice.WriteUV ( uvs[ index ], uvs[ index+1 ] );
			gfxDevice.WriteFinalColor4b();
		}
		gfxDevice.EndPrim();
	}
}

//----------------------------------------------------------------//
//Lua Registration
//----------------------------------------------------------------//
void	MOAISpineSkeletonSimple::RegisterLuaClass	( MOAILuaState& state ){
	UNUSED( state );
}

void	MOAISpineSkeletonSimple::RegisterLuaFuncs	( MOAILuaState& state ){
	MOAISpineSkeletonBase::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ NULL, NULL }
	};
	luaL_register ( state, 0, regTable );
}



//----------------------------------------------------------------//
//----------------------------------------------------------------//
//MOAISpineBoneHandle
//----------------------------------------------------------------//
//----------------------------------------------------------------//
void MOAISpineBoneHandle::SyncTransform() {	
	if( (this->mLockFlags & MOAISpineBoneHandle::LOCK_LOC) == 0 ) {
		this->SetLoc( mBone->worldX, mBone->worldY, 0.0f );
	}	else {
		ZLVec3D loc = this->GetLoc();
		mBone->x = loc.mX;
		mBone->y = loc.mY;
	}

	if( (this->mLockFlags & MOAISpineBoneHandle::LOCK_ROT) == 0 ) {
		this->SetRot( 0.0f, 0.0f, mBone->worldRotation );
	}	else {
		ZLVec3D rot = this->GetRot();
		mBone->rotation = rot.mZ;
	}

	if( (this->mLockFlags & MOAISpineBoneHandle::LOCK_SCL) == 0 ) {
		this->SetScl( mBone->worldScaleX, mBone->worldScaleY, 1.0f );
	}	else  {
		ZLVec3D scl = this->GetScl();
		mBone->scaleX = scl.mX;
		mBone->scaleY = scl.mY;
	}	
}

void MOAISpineBoneHandle::UpdateTimelineFilter() {
	//TODO
}


//----------------------------------------------------------------//
//----------------------------------------------------------------//
//MOAISpineSlot
//----------------------------------------------------------------//
//----------------------------------------------------------------//

int MOAISpineSlot::_lockVisible ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	if ( state.GetValue< bool >( 2, true ) ) {
		self->mLockFlags |= LOCK_VISIBLE;
	} else {
		self->mLockFlags &= ~LOCK_VISIBLE;
	}
	return 0;
}

int MOAISpineSlot::_lockAttachment ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	if ( state.GetValue< bool >( 2, true ) ) {
		self->mLockFlags |= LOCK_ATTACHMENT;
	} else {
		self->mLockFlags &= ~LOCK_ATTACHMENT;
	}
	self->UpdateTimelineFilter();
	return 0;
}

int MOAISpineSlot::_lockColor ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	if ( state.GetValue< bool >( 2, true ) ) {
		self->mLockFlags |= LOCK_COLOR;
	} else {
		self->mLockFlags &= ~LOCK_COLOR;
	}
	self->UpdateTimelineFilter();
	return 0;
}

int MOAISpineSlot::_lockTransform ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	if ( state.GetValue< bool >( 2, true ) ) {
		self->mLockFlags |= LOCK_LOC;
	} else {
		self->mLockFlags &= ~LOCK_LOC;
	}
	
	if ( state.GetValue< bool >( 3, true ) ) {
		self->mLockFlags |= LOCK_ROT;
	} else {
		self->mLockFlags &= ~LOCK_ROT;
	}

	if ( state.GetValue< bool >( 4, true ) ) {
		self->mLockFlags |= LOCK_SCL;
	} else {
		self->mLockFlags &= ~LOCK_SCL;
	}
	return 0;
}

int MOAISpineSlot::_getName ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )	
	lua_pushstring( L, self->mSlot->data->name );	
	return 1;
}

int MOAISpineSlot::_getBoneName ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	lua_pushstring( L, bone->data->name );	
	return 1;
}

int MOAISpineSlot::_getBoneParentName ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	if( !bone->parent ) return 0;
	lua_pushstring( L, bone->parent->data->name );	
	return 1;
}

int MOAISpineSlot::_getBoneLoc ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	state.Push( bone->x );
	state.Push( bone->y );
	return 2;
}

int MOAISpineSlot::_getBoneScl ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	state.Push( bone->scaleX );
	state.Push( bone->scaleY );
	return 2;
}

int MOAISpineSlot::_getBoneRot ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	state.Push( bone->rotation );
	return 1;
}

int MOAISpineSlot::_getBoneWorldLoc ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	state.Push( bone->worldX );
	state.Push( bone->worldY );
	return 2;
}

int MOAISpineSlot::_getBoneWorldScl ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	state.Push( bone->worldScaleX );
	state.Push( bone->worldScaleY );
	return 2;
}

int MOAISpineSlot::_getBoneWorldRot ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	state.Push( bone->worldRotation );
	return 1;
}

int MOAISpineSlot::_getBoneLength ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "U" )
	Bone* bone = self->mSlot->bone;
	state.Push( bone->data->length );
	return 1;
}

int MOAISpineSlot::_setBoneLoc ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "UNN" )
	Bone* bone = self->mSlot->bone;
	float x = state.GetValue < float > ( 2, 0 );
	float y = state.GetValue < float > ( 3, 0 );
	bone->x = x;
	bone->y = y;
	return 0;
}

int MOAISpineSlot::_setBoneScl ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "UNN" )
	Bone* bone = self->mSlot->bone;
	float x = state.GetValue < float > ( 2, 0 );
	float y = state.GetValue < float > ( 3, 0 );
	bone->scaleX = x;
	bone->scaleY = y;
	return 0;
}

int MOAISpineSlot::_setBoneRot ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSlot, "UN" )
	Bone* bone = self->mSlot->bone;
	float rotation = state.GetValue < float > ( 2, 0 );
	bone->rotation = rotation;
	return 0;
}

//----------------------------------------------------------------//
void MOAISpineSlot::SetDeck( MOAIDeck* deck ) {
	this->mDeck.Set ( *this, deck );
	// if ( this->mDeck ) {
	// 	this->SetMask ( this->mDeck->GetContentMask ());
	// }
	// else {
	// 	this->SetMask ( 0 );
	// }
}

MOAISpineSlot::MOAISpineSlot()
	:mLockFlags( 0 ), mSlot( 0 )
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAIGraphicsProp )
	RTTI_END
}

MOAISpineSlot::~MOAISpineSlot() {
}

//----------------------------------------------------------------//
void	MOAISpineSlot::RegisterLuaClass	( MOAILuaState& state ){
	MOAIGraphicsProp::RegisterLuaClass( state );
}

void	MOAISpineSlot::RegisterLuaFuncs	( MOAILuaState& state ){
	MOAIGraphicsProp::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "lockVisible",       _lockVisible   },
		{ "lockAttachment",    _lockAttachment},
		{ "lockColor",         _lockColor     },
		{ "lockTransform",     _lockTransform },
		{ "getName",           _getName       },
		{ "getBoneName",       _getBoneName   },
		{ "getBoneParentName", _getBoneParentName },
		{ "setBoneRot",        _setBoneRot      },
		{ "setBoneLoc",        _setBoneLoc      },
		{ "setBoneScl",        _setBoneScl      },
		{ "getBoneRot",        _getBoneRot      },
		{ "getBoneLoc",        _getBoneLoc      },
		{ "getBoneScl",        _getBoneScl      },
		{ "getBoneWorldRot",   _getBoneWorldRot },
		{ "getBoneWorldLoc",   _getBoneWorldLoc },
		{ "getBoneWorldScl",   _getBoneWorldScl },
		{ "getBoneLength",     _getBoneLength },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
void MOAISpineSlot::SetAdditiveBlend() {
	this->mBlendMode.SetBlend ( MOAIBlendMode::BLEND_ADD );
}

void MOAISpineSlot::SetAlphaBlend() {
	this->mBlendMode.SetBlend ( ZGL_BLEND_FACTOR_SRC_ALPHA, ZGL_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA );
}

void MOAISpineSlot::SetNormalBlend() {
	this->mBlendMode.SetBlend ( MOAIBlendMode::BLEND_NORMAL );
}

//----------------------------------------------------------------//
u32 MOAISpineSlot::OnGetModelBounds ( ZLBox& bounds ) {
	if( this->GetDeck() ){
		return MOAIProp::OnGetModelBounds( bounds );
	} else {
		return GetAttachmentBounds( bounds );
	}
}

u32 MOAISpineSlot::GetAttachmentBounds  ( ZLBox& bounds ) {
	//TODO:!!!
	if( !mSlot->attachment ) return BOUNDS_EMPTY;	
	// if( mSlot->attachment->type == ATTACHMENT_REGION ) {
	// } else if( mSlot->attachment->type == ATTACHMENT_MESH ) {
	// } else if( mSlot->attachment->type == ATTACHMENT_SKINNED_MESH ) {
	// }
	// return BOUNDS_OK;
	return BOUNDS_GLOBAL;
}

void MOAISpineSlot::SetSlot( Slot* slot ) {
	mSlot = slot;

	if( !slot->attachment ) return;
	if( mSlot->attachment->type == ATTACHMENT_REGION ) {
		RegionAttachment *region = (RegionAttachment*)mSlot->attachment;
		mTexture.Set( *this,
			(MOAITexture*) ((AtlasRegion*) region->rendererObject) ->rendererObject
		);

	} else if( mSlot->attachment->type == ATTACHMENT_MESH ) {
		MeshAttachment *mesh     = (MeshAttachment*)slot->attachment;	
		mTexture.Set( *this,
			(MOAITexture*) ((AtlasRegion*) mesh->rendererObject) ->rendererObject
		);

	} else if( mSlot->attachment->type == ATTACHMENT_SKINNED_MESH ) {
		SkinnedMeshAttachment *mesh     = (SkinnedMeshAttachment*)slot->attachment;
		mTexture.Set( *this,
			(MOAITexture*) ((AtlasRegion*) mesh->rendererObject) ->rendererObject
		);
	}

	mShader.Set( *this,
		&MOAIShaderMgr::Get ().GetShader ( MOAIShaderMgr::DECK2D_SHADER )
	);
	
}

void MOAISpineSlot::Draw( int subPrimId, float lod ) {
	if( this->GetDeck() ) {
		MOAIGraphicsProp::Draw( subPrimId, lod );
	} else {
		if( !mSlot->attachment ) return ;
		if ( !this->IsVisible ( lod )) return;

		if( mSlot->attachment->type == ATTACHMENT_REGION ) {
			this->DrawRegionAttachment();
		} else if( mSlot->attachment->type == ATTACHMENT_MESH ) {
			this->DrawMeshAttachment();
		} else if( mSlot->attachment->type == ATTACHMENT_SKINNED_MESH ) {
			this->DrawSkinnedMeshAttachment();
		}
	}
}

void MOAISpineSlot::DrawRegionAttachment () {
	Slot* slot = mSlot;
	RegionAttachment *region = (RegionAttachment*)slot->attachment;
	MOAITexture* texture     = (MOAITexture*) ((AtlasRegion*) region->rendererObject) ->rendererObject;
	mTexture.Set( *this, texture );

	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
	this->LoadGfxState ();
	this->LoadVertexTransform ();
	// gfxDevice.SetGfxState( texture );
		
	gfxDevice.SetVertexPreset ( MOAIVertexFormatMgr::XYZWUVC );
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );
	gfxDevice.BeginPrim ( ZGL_PRIM_TRIANGLES );

		gfxDevice.WriteVtx ( region->offset[VERTEX_X1], region->offset[VERTEX_Y1], 0.0f );
		gfxDevice.WriteUV ( region->uvs[VERTEX_X1], region->uvs[VERTEX_Y1] );
		gfxDevice.WriteFinalColor4b ();

		gfxDevice.WriteVtx ( region->offset[VERTEX_X2], region->offset[VERTEX_Y2], 0.0f );
		gfxDevice.WriteUV ( region->uvs[VERTEX_X2], region->uvs[VERTEX_Y2] );
		gfxDevice.WriteFinalColor4b ();
		
		gfxDevice.WriteVtx ( region->offset[VERTEX_X4], region->offset[VERTEX_Y4], 0.0f );
		gfxDevice.WriteUV ( region->uvs[VERTEX_X4], region->uvs[VERTEX_Y4] );
		gfxDevice.WriteFinalColor4b ();
	gfxDevice.EndPrim ();

	gfxDevice.BeginPrim ();
		gfxDevice.WriteVtx ( region->offset[VERTEX_X2], region->offset[VERTEX_Y2], 0.0f );
		gfxDevice.WriteUV ( region->uvs[VERTEX_X2], region->uvs[VERTEX_Y2] );
		gfxDevice.WriteFinalColor4b ();

		gfxDevice.WriteVtx ( region->offset[VERTEX_X3], region->offset[VERTEX_Y3], 0.0f );
		gfxDevice.WriteUV ( region->uvs[VERTEX_X3], region->uvs[VERTEX_Y3] );
		gfxDevice.WriteFinalColor4b ();
	
		gfxDevice.WriteVtx ( region->offset[VERTEX_X4], region->offset[VERTEX_Y4], 0.0f );
		gfxDevice.WriteUV ( region->uvs[VERTEX_X4], region->uvs[VERTEX_Y4] );
		gfxDevice.WriteFinalColor4b ();

	gfxDevice.EndPrim ();
}

void MOAISpineSlot::DrawMeshAttachment () {
	Slot* slot = mSlot;
	float worldVertices[ SPINE_MESH_VERTEX_COUNT_MAX ];
	MeshAttachment *mesh     = (MeshAttachment*)slot->attachment;	
	MOAITexture* texture     = (MOAITexture*) ((AtlasRegion*) mesh->rendererObject) ->rendererObject;
	mTexture.Set( *this, texture );

	ZLMatrix4x4 worldDrawingMtx;

	MeshAttachment_computeWorldVertices(
		mesh, slot->skeleton->x, slot->skeleton->y, slot, worldVertices
	);

	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
	this->LoadGfxState ();
	worldDrawingMtx.Init( this->mParentSkeleton->GetLocalToWorldMtx () );
	gfxDevice.SetVertexTransform ( MOAIGfxDevice::VTX_WORLD_TRANSFORM, worldDrawingMtx );
	
	gfxDevice.SetVertexPreset ( MOAIVertexFormatMgr::XYZWUVC );
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );

	gfxDevice.BeginPrim ( ZGL_PRIM_TRIANGLE_STRIP );
	
		for (int i = 0; i < mesh->trianglesCount; ++i) {
			int index = mesh->triangles[i] * 2;
			gfxDevice.WriteVtx ( worldVertices[ index ], worldVertices[ index+1 ], 0.0f );
			gfxDevice.WriteUV ( mesh->uvs[ index ], mesh->uvs[ index+1 ] );
			gfxDevice.WriteFinalColor4b ();
		}

	gfxDevice.EndPrim();
}

void MOAISpineSlot::DrawSkinnedMeshAttachment () {
	Slot* slot = mSlot;
	float worldVertices[ SPINE_MESH_VERTEX_COUNT_MAX ];
	SkinnedMeshAttachment *mesh     = (SkinnedMeshAttachment*)slot->attachment;
	MOAITexture* texture     = (MOAITexture*) ((AtlasRegion*) mesh->rendererObject) ->rendererObject;
	mTexture.Set( *this, texture );
	
	ZLMatrix4x4 worldDrawingMtx;

	SkinnedMeshAttachment_computeWorldVertices(
		mesh, slot->skeleton->x, slot->skeleton->y, slot, worldVertices
	);

	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get ();
	this->LoadGfxState ();
	worldDrawingMtx.Init( this->mParentSkeleton->GetLocalToWorldMtx () );
	gfxDevice.SetVertexTransform ( MOAIGfxDevice::VTX_WORLD_TRANSFORM, worldDrawingMtx );
	
	gfxDevice.SetVertexPreset ( MOAIVertexFormatMgr::XYZWUVC );
	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_PROJ );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );

	gfxDevice.BeginPrim ( ZGL_PRIM_TRIANGLE_STRIP );
	
		for (int i = 0; i < mesh->trianglesCount; ++i) {
			int index = mesh->triangles[i] * 2;
			gfxDevice.WriteVtx ( worldVertices[ index ], worldVertices[ index+1 ], 0.0f );
			gfxDevice.WriteUV ( mesh->uvs[ index ], mesh->uvs[ index+1 ] );
			gfxDevice.WriteFinalColor4b ();
		}

	gfxDevice.EndPrim();
}

void MOAISpineSlot::UpdateTimelineFilter() {
	u32 filter = 0;
	if( (this->mLockFlags & MOAISpineSlot::LOCK_COLOR) != 0 ) {
		filter |= SP_TIMELINE_FILTER_COLOR;
	}

	if( (this->mLockFlags & MOAISpineSlot::LOCK_ATTACHMENT) != 0 ) {
		filter |= SP_TIMELINE_FILTER_ATTACHMENT;
	}
	mSlot->timelineFilter = filter;
}


//----------------------------------------------------------------//
//----------------------------------------------------------------//
//MOAISpineSkeleton
//----------------------------------------------------------------//
//----------------------------------------------------------------//

int MOAISpineSkeleton::_getSlotProps ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeleton, "U" )
	if( !self->mSkeleton ) return 0;

	u32 count = self->mSkeleton->slotCount;
	for (int i = 0, n = count; i < n; i++) {
		Slot* slot = self->mSkeleton->slots[i];
		self->mSlotPropMap[ slot ]->PushLuaUserdata( state );
	}
	return count;
}

int MOAISpineSkeleton::_findSlotProp ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeleton, "US" )
	if( !self->mSkeleton ) return 0;
	cc8* slotName = lua_tostring( L, 2 );
	MOAISpineSlot* prop = self->FindSlotProp( slotName );
	if( !prop ) return 0;
	prop->PushLuaUserdata( state );
	return 1;
}

int MOAISpineSkeleton::_forceUpdateSlots( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeleton, "U" )
	SlotPropIt it = self->mSlotPropMap.begin ();
	for ( ; it != self->mSlotPropMap.end (); ++it ) {
		it->second->ForceUpdate();
	}
	return 0;
}


int MOAISpineSkeleton::_requestBoneHandle ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeleton, "US" )
	if( !self->mSkeleton ) return 0;
	cc8* slotName = lua_tostring( L, 2 );
	MOAISpineSlot* prop = self->FindSlotProp( slotName );
	if( !prop ) return 0;
	prop->PushLuaUserdata( state );
	return 1;
}


//----------------------------------------------------------------//
//Lua Registration
//----------------------------------------------------------------//
void	MOAISpineSkeleton::RegisterLuaClass	( MOAILuaState& state ){
	UNUSED( state );
}

void	MOAISpineSkeleton::RegisterLuaFuncs	( MOAILuaState& state ){
	MOAISpineSkeletonBase::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "getSlotProps",          _getSlotProps },
		{ "findSlotProp",          _findSlotProp },		
		{ "requestBoneHandle",     _requestBoneHandle },
		{ "forceUpdateSlots",      _forceUpdateSlots },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
// Ctor, Dtor
//----------------------------------------------------------------//
MOAISpineSkeleton::MOAISpineSkeleton()
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAISpineSkeletonBase )
	RTTI_END
	mShader.Set( *this,
		&MOAIShaderMgr::Get ().GetShader ( MOAIShaderMgr::DECK2D_SHADER )
	);
}

MOAISpineSkeleton::~MOAISpineSkeleton() {	
	this->Unload();
}

//----------------------------------------------------------------//
void MOAISpineSkeleton::OnLoad( MOAISpineSkeletonData* data, float ZScale ) {	
	//build prop for each slot
	for (int i = 0, n = mSkeleton->slotCount; i < n; i++) {
		Slot* slot = mSkeleton->slots[i];
		MOAISpineSlot* prop = new MOAISpineSlot();
		LuaRetain( prop );
		prop->mParentSkeleton = this;
		prop->SetSlot( slot );
		mSlotPropMap[ slot ] = prop;
		prop->SetAttrLink ( PACK_ATTR ( MOAIColor, INHERIT_COLOR ),         this, PACK_ATTR ( MOAIColor, COLOR_TRAIT )             );
		prop->SetAttrLink ( PACK_ATTR ( MOAIGraphicsProp, INHERIT_VISIBLE ),        this, PACK_ATTR ( MOAIGraphicsProp, ATTR_VISIBLE )             );
		prop->SetAttrLink ( PACK_ATTR ( MOAIProp, ATTR_PARTITION ),         this, PACK_ATTR ( MOAIProp, ATTR_PARTITION )           );
		prop->SetAttrLink ( PACK_ATTR ( MOAIGraphicsProp, ATTR_SHADER ),            this, PACK_ATTR ( MOAIGraphicsProp, ATTR_SHADER )              );
		// prop->SetAttrLink ( PACK_ATTR ( MOAIGraphicsProp, ATTR_BLEND_MODE ),        this, PACK_ATTR ( MOAIGraphicsProp, ATTR_BLEND_MODE )          );
		prop->SetAttrLink ( PACK_ATTR ( MOAITransform, INHERIT_TRANSFORM ), this, PACK_ATTR ( MOAITransformBase, TRANSFORM_TRAIT ) );
		
		if( slot->data->additiveBlending ) {
			prop->SetAdditiveBlend();
		} else {
			prop->SetAlphaBlend();			
		}
		
		prop->SetPriority( i );
		prop->SetZLoc( (float)i * ZScale );
	}
	UpdateSpine();
}

//----------------------------------------------------------------//
void MOAISpineSkeleton::OnUnload() {
	// printf("unload skeleton\n");
	BoneHandleIt boneIt = mBoneHandleMap.begin ();
	for ( ; boneIt != mBoneHandleMap.end (); ++boneIt ) {
		LuaRelease( boneIt->second );
	} 
	mBoneHandleMap.clear();

	SlotPropIt slotIt = mSlotPropMap.begin ();
	for ( ; slotIt != mSlotPropMap.end (); ++slotIt ) {
		LuaRelease( slotIt->second );
	} 
	mSlotPropMap.clear();
	if( mSkeleton ) {
		Skeleton_dispose( mSkeleton );
		mSkeleton = NULL;
	}
}

//----------------------------------------------------------------//
void MOAISpineSkeleton::UpdateSpine() {
	if( !mSkeleton ) return;
	//update bone
	BoneHandleIt boneIt = mBoneHandleMap.begin ();
	for ( ; boneIt != mBoneHandleMap.end (); ++boneIt ) {
		MOAISpineBoneHandle* handle = boneIt->second;
		handle->SyncTransform();
	}
	Skeleton_updateWorldTransform( mSkeleton );

	//update slot props
	SlotPropIt slotIt = mSlotPropMap.begin ();
	for ( ; slotIt != mSlotPropMap.end (); ++slotIt ) {
		Slot*     slot = slotIt->first;
		Bone*     bone = slot->bone;

		MOAISpineSlot* prop = slotIt->second;
		if( (prop->mLockFlags & MOAISpineSlot::LOCK_LOC) == 0 ) {
			ZLVec3D loc = prop->GetLoc();
			loc.mX = bone->worldX;
			loc.mY = bone->worldY;
			prop->SetLoc( loc );
		}

		if( (prop->mLockFlags & MOAISpineSlot::LOCK_ROT) == 0 ) {
			ZLVec3D rot = prop->GetRot();
			rot.mZ = bone->worldRotation;
			prop->SetRot( rot );
		}
		
		if( (prop->mLockFlags & MOAISpineSlot::LOCK_SCL) == 0 ) {
			ZLVec3D scl = prop->GetScl();
			scl.mX = bone->worldScaleX;
			scl.mY = bone->worldScaleY;
			prop->SetScl( scl );
		}
		
		if( (prop->mLockFlags & MOAISpineSlot::LOCK_COLOR) == 0 ) {
			prop->Set( slot->r, slot->g, slot->b, slot->a );
		}
		
		prop->ScheduleUpdate();
	}
}

//----------------------------------------------------------------//
MOAISpineSlot* MOAISpineSkeleton::FindSlotProp( const char* slotName ) {
	if( !mSkeleton ) return NULL;
	Slot* slot = Skeleton_findSlot( mSkeleton, slotName );
	if( !slot ) return NULL;
	return mSlotPropMap[ slot ];
}

//----------------------------------------------------------------//
MOAISpineBoneHandle* MOAISpineSkeleton::RequestBoneHandle( const char* boneName ) {
	if( !mSkeleton ) return NULL;
	Bone* bone = Skeleton_findBone( mSkeleton, boneName );
	if( !bone ) return NULL;
	MOAISpineBoneHandle* handle = mBoneHandleMap[ bone ];
	if( !handle ) {
		handle = new MOAISpineBoneHandle();
		handle->mBone = bone;
		mBoneHandleMap[ bone ] = handle;
		LuaRetain( handle );
	}
	return handle;
}


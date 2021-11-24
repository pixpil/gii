#include "MOCKProp.h"


//----------------------------------------------------------------//
int MOCKProp::_setWorldLoc( lua_State *L ){
	MOAI_LUA_SETUP ( MOCKProp, "U" )
	ZLVec3D loc = state.GetVec3D ( 2, 0.0f );
	self->SetWorldLoc( loc );
	return 0;
}

int MOCKProp::_setWorldRot( lua_State *L ) {
	MOAI_LUA_SETUP ( MOCKProp, "U" )
	float rot = state.GetValue( 2, 0.0f );
	self->SetWorldRot(rot);
	return 0;
}

//----------------------------------------------------------------//
MOCKProp::MOCKProp () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIGraphicsProp )
	RTTI_END
}

MOCKProp::~MOCKProp () {

}


float GetRotZ( const ZLAffine3D& aff ) {
	float rot = ( float )( atan2 ( aff.m[ ZLAffine3D::C0_R1 ], aff.m[ ZLAffine3D::C0_R0 ] ) * R2D );
	return rot;
}

//----------------------------------------------------------------//
bool MOCKProp::ApplyAttrOp ( u32 attrID, MOAIAttrOp& attrOp, u32 op ) {
	if ( MOAITransformBaseAttr::Check ( attrID )) {

		switch ( UNPACK_ATTR ( attrID )) {
			case ATTR_WORLD_Z_ROT: {
				float rot = GetRotZ( this->mLocalToWorldMtx );
				attrOp.Apply ( rot, op, MOAIAttrOp::ATTR_READ, MOAIAttrOp::ATTR_TYPE_FLOAT );
				return true;
			}
		}

	}
	return MOAIGraphicsProp::ApplyAttrOp( attrID, attrOp, op );
}


//----------------------------------------------------------------//
void MOCKProp::OnDepNodeUpdate () {
	const ZLAffine3D* src = this->GetLinkedValue < ZLAffine3D* >( MOCKPropAttr::Pack ( SYNC_WORLD_LOC ), 0 );
	if ( src ) {
		this->SetWorldLoc( src->GetTranslation() );
		//TODO: scl/rotation
	} else {
		src = this->GetLinkedValue < ZLAffine3D* >( MOCKPropAttr::Pack ( SYNC_WORLD_LOC_2D ), 0 );
		if( src ) {
			this->SetWorldTransform2D( *src );
			// float z0 = this->mLoc.mZ;
			// this->SetWorldLoc( src->GetTranslation() );
			// this->mLoc.mZ = z0;
			// this->mRot.mZ = 
		}
	}
	MOAIGraphicsProp::OnDepNodeUpdate();
}

MOAITransformBase* MOCKProp::FindParentTransform () {
	MOAITransformBase* parent = NULL;
	MOAIDepLink* link;
	//try INHERIT_TRANSFORM
	link = this->FindAttrLink ( PACK_ATTR ( MOAITransformBase, MOAITransformBase::INHERIT_TRANSFORM ) );
	if ( link && link->GetSourceNode() ) {
		parent = link->GetSourceNode()->AsType < MOAITransformBase >();		
	}
	//try INHERIT_LOC
	if ( !parent ) {
		link = this->FindAttrLink ( PACK_ATTR ( MOAITransformBase, MOAITransformBase::INHERIT_LOC ) );
		if ( link && link->GetSourceNode() ) {
			parent = link->GetSourceNode()->AsType < MOAITransformBase >();
		}
	}

	return parent;
}

void MOCKProp::SetWorldLoc( const ZLVec3D& loc ) {
	MOAITransformBase* parent = this->FindParentTransform();

	if ( parent ) {
		parent->DepNodeUpdate();
		const ZLAffine3D& aff = parent->GetWorldToLocalMtx();
		ZLVec3D local = loc;
		aff.Transform( local );
		this->SetLoc( local );

	} else {
		this->SetLoc( loc );

	}

	this->ScheduleUpdate();
}

void MOCKProp::SetWorldRot( float rotation )
{
	MOAITransformBase* parent = this->FindParentTransform();

	if ( parent ) {
		parent->DepNodeUpdate();
		float parentRot = parent->GetLocalToWorldMtx().GetRot();
		ZLVec3D oldRot = this->GetRot();
		this->SetRot(oldRot.mX, oldRot.mY, rotation - parentRot);
	} else {
		ZLVec3D oldRot = this->GetRot();
		this->SetRot(oldRot.mX, oldRot.mY, rotation);
	}
}


void MOCKProp::SetWorldTransform2D( const ZLAffine3D& mtx ) {
	MOAITransformBase* parent = this->FindParentTransform();

	if ( parent ) {
		parent->DepNodeUpdate();
		const ZLAffine3D& parentMtx = parent->GetWorldToLocalMtx();
		ZLVec3D local = mtx.GetTranslation();
		parentMtx.Transform( local );
		float z0 = this->mLoc.mZ;
		local.mZ = z0;
		this->SetLoc( local );

		
		ZLVec3D front = mtx.GetHeading();
		parentMtx.TransformVec( front );

		float rz = atan2 ( front.mY, front.mX ) * R2D;
		this->mRot.mZ = rz;

	} else {

		float z0 = this->mLoc.mZ;
		this->SetLoc( mtx.GetTranslation() );
		this->mLoc.mZ = z0;
		this->mRot.mZ = GetRotZ( mtx );

	}

	this->ScheduleUpdate();
}

//----------------------------------------------------------------//
void MOCKProp::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIGraphicsProp::RegisterLuaClass ( state );
	state.SetField ( -1, "SYNC_WORLD_LOC",	  MOCKPropAttr::Pack ( SYNC_WORLD_LOC )   );
	state.SetField ( -1, "SYNC_WORLD_LOC_2D",	MOCKPropAttr::Pack ( SYNC_WORLD_LOC_2D ));
}

void MOCKProp::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIGraphicsProp::RegisterLuaFuncs ( state );

	luaL_Reg regTable [] = {
		{ "setWorldLoc",         _setWorldLoc },
		{ "setWorldRot", 				 _setWorldRot },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );

}

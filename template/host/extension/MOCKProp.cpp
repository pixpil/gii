#include "MOCKProp.h"


//----------------------------------------------------------------//
int MOCKProp::_setWorldLoc( lua_State *L ){
	MOAI_LUA_SETUP ( MOCKProp, "U" )
	ZLVec3D loc = state.GetVec3D ( 2, 0.0f );
	self->SetWorldLoc( loc );
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

//----------------------------------------------------------------//
bool MOCKProp::ApplyAttrOp ( u32 attrID, MOAIAttrOp& attrOp, u32 op ) {
	if ( MOAITransformBaseAttr::Check ( attrID )) {

		switch ( UNPACK_ATTR ( attrID )) {
			case ATTR_WORLD_X_LOC:
				break;

			case ATTR_WORLD_Y_LOC:
				break;

			case ATTR_WORLD_Z_LOC:
				break;

			case ATTR_WORLD_Z_ROT:
				break;
			
		}
	}
	return MOAIGraphicsProp::ApplyAttrOp( attrID, attrOp, op );
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

//----------------------------------------------------------------//
void MOCKProp::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIGraphicsProp::RegisterLuaClass ( state );
}

void MOCKProp::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIGraphicsProp::RegisterLuaFuncs ( state );

	luaL_Reg regTable [] = {
		{ "setWorldLoc",         _setWorldLoc },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );

}

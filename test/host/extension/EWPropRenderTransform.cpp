#include "EWPropRenderTransform.h"

int EWPropRenderTransform::_setLogicTransform ( lua_State *L ) {
	MOAI_LUA_SETUP( EWPropRenderTransform, "UU" )
	MOAITransformBase* trans = state.GetLuaObject < MOAITransformBase >( 2, 0 );
	if( trans ) {
		self->mLogicTransform.Set( *self, trans );
		self->SetNodeLink( *trans );
	}
	return 0;
}

int EWPropRenderTransform::_setFloorViewMode ( lua_State *L ) {
	MOAI_LUA_SETUP( EWPropRenderTransform, "UB" )
	self->mFloorViewMode = state.GetValue < bool >( 2, true );
	self->ScheduleUpdate();
	return 0;
}

int EWPropRenderTransform::_setRoundStep ( lua_State *L ) {
	MOAI_LUA_SETUP( EWPropRenderTransform, "UN" )
	self->mRoundStep = state.GetValue < float >( 2, 1.0f );
	self->ScheduleUpdate();
	return 0;
}

int EWPropRenderTransform::_setSyncRot ( lua_State *L ) {
	MOAI_LUA_SETUP( EWPropRenderTransform, "UB" )
	self->mFlagSyncRot = state.GetValue < bool >( 2, true );
	self->ScheduleUpdate();
	return 0;
}
//----------------------------------------------------------------//
EWPropRenderTransform::EWPropRenderTransform () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIGraphicsProp )
	RTTI_END
	this->mFlagSyncRot = false;
	this->mFloorViewMode = false;
	this->mRoundStep = 2.0;
}

EWPropRenderTransform::~EWPropRenderTransform () {
	this->mLogicTransform.Set( *this, 0 );
}


void EWPropRenderTransform::BuildLocalToWorldMtx ( ZLAffine3D& localToWorldMtx ) {
	if( !this->mLogicTransform ) return;
	const ZLAffine3D& logicMtx = this->mLogicTransform->GetLocalToWorldMtx();

	float x, y, z;
	x = ( float )logicMtx.m[ ZLAffine3D::C3_R0 ];
	y = ( float )logicMtx.m[ ZLAffine3D::C3_R1 ];
	z = ( float )logicMtx.m[ ZLAffine3D::C3_R2 ];
	
	ZLAffine3D localMtx;
	localMtx.ScRoTr (
		this->mScale.mX,
		this->mScale.mY,
		this->mScale.mZ,
		ClampEuler ( this->mRot.mX ) * ( float )D2R,
		ClampEuler ( this->mRot.mY ) * ( float )D2R,
		ClampEuler ( this->mRot.mZ ) * ( float )D2R,
		0.0f,
		0.0f,
		0.0f
	);
		
	if( !this->mFlagSyncRot ) {
		localToWorldMtx.Ident();
		// localToWorldMtx.Init ( logicMtx );
		//copy Scale
		// localToWorldMtx.m[ ZLAffine3D::C0_R0 ] = logicMtx.m[ ZLAffine3D::C0_R0 ];
		// localToWorldMtx.m[ ZLAffine3D::C1_R1 ] = logicMtx.m[ ZLAffine3D::C1_R1 ];
		// localToWorldMtx.m[ ZLAffine3D::C2_R2 ] = logicMtx.m[ ZLAffine3D::C2_R2 ];
	} else {
		localToWorldMtx.Init ( logicMtx );
	}
	// ZLAffine3D shear;
	// shear.Shear ( this->mShearYX, this->mShearZX, this->mShearXY, this->mShearZY, this->mShearXZ, this->mShearYZ );
	// localToWorldMtx.Prepend ( shear );
	
	// if (( this->mPiv.mX != 0.0f ) || ( this->mPiv.mY != 0.0f ) || ( this->mPiv.mZ != 0.0f )) {
		
	// 	ZLAffine3D pivot;
	// 	pivot.Translate ( -this->mPiv.mX, -this->mPiv.mY, -this->mPiv.mZ );
	// }
	localToWorldMtx.Prepend ( localMtx );
	if( this->mFloorViewMode ) {
		ZLAffine3D floorMtx;
		floorMtx.ScRoTr(
			1.0f, 1.414f, 1.0f,
			-45.0f * (float)D2R, 0.0f, 0.0f,
			0.0f, 0.0f, 0.0f
			);
		localToWorldMtx.Append ( floorMtx );
	}
	//translate
	// localToWorldMtx.m[ ZLAffine3D::C3_R0 ] = floor( this->mLoc.mX + x       + 0.5f );
	// localToWorldMtx.m[ ZLAffine3D::C3_R1 ] = floor( this->mLoc.mY + (y + z) + 0.5f );
	// localToWorldMtx.m[ ZLAffine3D::C3_R2 ] = floor( this->mLoc.mZ + ( -y )  + 0.5f );

	// localToWorldMtx.m[ ZLAffine3D::C3_R0 ] = this->mLoc.mX + x       ;
	// localToWorldMtx.m[ ZLAffine3D::C3_R1 ] = this->mLoc.mY + (y + z) ;
	// localToWorldMtx.m[ ZLAffine3D::C3_R2 ] = this->mLoc.mZ + ( -y )  ;

	// localToWorldMtx.m[ ZLAffine3D::C3_R0 ] = floor( this->mLoc.mX + x       + 0.5f );
	// localToWorldMtx.m[ ZLAffine3D::C3_R1 ] = floor( this->mLoc.mY + (y + z) + 0.5f );
	// localToWorldMtx.m[ ZLAffine3D::C3_R2 ] = floor( this->mLoc.mZ + ( -y )  + 0.5f );

	localToWorldMtx.m[ ZLAffine3D::C3_R0 ] = floor( ( this->mLoc.mX + x       ) * this->mRoundStep ) / this->mRoundStep;
	localToWorldMtx.m[ ZLAffine3D::C3_R1 ] = floor( ( this->mLoc.mY + (y + z) ) * this->mRoundStep ) / this->mRoundStep;
	localToWorldMtx.m[ ZLAffine3D::C3_R2 ] = floor( ( this->mLoc.mZ + ( -y )  ) * this->mRoundStep ) / this->mRoundStep;
	
}


void EWPropRenderTransform::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIGraphicsProp::RegisterLuaClass ( state );
}

void EWPropRenderTransform::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIGraphicsProp::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "setLogicTransform",		_setLogicTransform },
		{ "setSyncRot",	         	_setSyncRot },
		{ "setFloorViewMode",    	_setFloorViewMode },
		{ "setRoundStep",    	    _setRoundStep },

		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

#include "EWProp.h"


EWProp::EWProp () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIGraphicsProp )
	RTTI_END
}

EWProp::~EWProp () {

}

void EWProp::BuildLocalToWorldMtx ( ZLAffine3D& localToWorldMtx ) {
	float x, y, z;
	x = this->mLoc.mX;
	y = this->mLoc.mY + this->mLoc.mZ;
	z = - this->mLoc.mY;

	localToWorldMtx.ScRoTr (
		this->mScale.mX,
		this->mScale.mY,
		this->mScale.mZ,
		ClampEuler ( this->mRot.mX ) * ( float )D2R,
		ClampEuler ( this->mRot.mY ) * ( float )D2R,
		ClampEuler ( this->mRot.mZ ) * ( float )D2R,
		x,
		y,
		z
	);
	
	// ZLAffine3D shear;
	// shear.Shear ( this->mShearYX, this->mShearZX, this->mShearXY, this->mShearZY, this->mShearXZ, this->mShearYZ );
	// localToWorldMtx.Prepend ( shear );
	
	// if (( this->mPiv.mX != 0.0f ) || ( this->mPiv.mY != 0.0f ) || ( this->mPiv.mZ != 0.0f )) {
		
	// 	ZLAffine3D pivot;
	// 	pivot.Translate ( -this->mPiv.mX, -this->mPiv.mY, -this->mPiv.mZ );
	// 	localToWorldMtx.Prepend ( pivot );
	// }
}


void EWProp::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIGraphicsProp::RegisterLuaClass ( state );
}

void EWProp::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIGraphicsProp::RegisterLuaFuncs ( state );
}

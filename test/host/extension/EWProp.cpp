#include "EWProp.h"

EWProp::EWProp () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOCKProp )
	RTTI_END
}

EWProp::~EWProp () {
}


// void EWProp::OnDepNodeUpdate () {
// 	MOCKProp::OnDepNodeUpdate();
// }


void EWProp::RegisterLuaClass ( MOAILuaState& state ) {
	MOCKProp::RegisterLuaClass ( state );
}

void EWProp::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOCKProp::RegisterLuaFuncs ( state );
}

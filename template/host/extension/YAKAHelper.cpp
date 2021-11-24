#include <YAKAHelper.h>

int YAKAHelper::_distanceBetweenTransform(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UU" )) return 0;
	MOAITransform* t1 = state.GetLuaObject<MOAITransform>(1,true);
	MOAITransform* t2 = state.GetLuaObject<MOAITransform>(2,true);
	if( !t1 || !t2 ) return 0;
	ZLVec3D v1 = t1->GetLoc();
	ZLVec3D v2 = t2->GetLoc();
	float dst = (v1 - v2).Length();
	state.Push(dst);
	return 1;
}

int YAKAHelper::_mixColor(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UUN" )) return 0;
	MOAIColor* t1 = state.GetLuaObject<MOAIColor>(1,true);
	MOAIColor* t2 = state.GetLuaObject<MOAIColor>(2,true);
	if( !t1 || !t2 ) return 0;
	float weight  = state.GetValue<float>( 3, 1.0f );
	u32 mode = state.GetValue<u32>( 4, ZLInterpolate::kLinear );
	t1->Lerp( mode, *t1, *t2, weight );
	return 0;
}


int YAKAHelper::_addColor(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UUN" )) return 0;
	MOAIColor* t1 = state.GetLuaObject<MOAIColor>(1,true);
	MOAIColor* t2 = state.GetLuaObject<MOAIColor>(2,true);
	if( !t1 || !t2 ) return 0;
	float weight  = state.GetValue<float>( 3, 1.0f );
	t1->mR = min( 1.0f, t1->mR + t2->mR * weight );
	t1->mG = min( 1.0f, t1->mG + t2->mG * weight );
	t1->mB = min( 1.0f, t1->mB + t2->mB * weight );
	// t1->mA += min( 1.0f, t2->mA * weight );
	t1->ScheduleUpdate();
	return 0;
}

int YAKAHelper::_blockAction(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UU" )) return 0;

	MOAIAction *blocked = state.GetLuaObject<MOAIAction>(1,true);
	MOAIAction *blocker = state.GetLuaObject<MOAIAction>(2,true);

	if(blocked && blocker){
		blocked->SetBlocker(blocker);
	}

	return 0;
}

YAKAHelper::YAKAHelper(){
	RTTI_BEGIN
		RTTI_SINGLE(MOAILuaObject)
	RTTI_END
}

YAKAHelper::~YAKAHelper(){}

void YAKAHelper::RegisterLuaClass(MOAILuaState &state){
	luaL_Reg regTable [] = {		
		{	"distanceBetweenTransform", _distanceBetweenTransform},
		{	"mixColor",                 _mixColor},
		{	"addColor",                 _addColor},
		{	"blockAction",              _blockAction},
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}


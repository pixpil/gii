#include "MOAISpineAnimationMixTable.h"


//----------------------------------------------------------------//
//@ self
//string src 
//string target
//float  duration 
//float  delay
int MOAISpineAnimationMixTable::_setMix ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimationMixTable, "USSN" )
	STLString src    = lua_tostring( state, 2 );
	STLString target = lua_tostring( state, 3 );
	float duration = state.GetValue< float >( 4, 0.0f );
	float delay    = state.GetValue< float >( 5, 0.0f );
	MOAISpineAnimationMixEntry* entry = self->AffirmMix( src, target );
	entry->mSrc    = src;
	entry->mTarget = target;
	entry->mDuration = duration;
	entry->mDelay    = delay;
	return 0;
}


int MOAISpineAnimationMixTable::_getMix ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimationMixTable, "USS" )
	STLString src    = lua_tostring( state, 2 );
	STLString target = lua_tostring( state, 3 );
	MOAISpineAnimationMixEntry* entry = self->GetMix( src, target );
	if( entry ) {
		state.Push( entry->mDuration );
		state.Push( entry->mDelay );
		return 2;
	}
	return 0;
}



//----------------------------------------------------------------//
//Lua Registration
//----------------------------------------------------------------//
void	MOAISpineAnimationMixTable::RegisterLuaClass	( MOAILuaState& state ){
	UNUSED( state );
}

void	MOAISpineAnimationMixTable::RegisterLuaFuncs	( MOAILuaState& state ){
	luaL_Reg regTable [] = {
		{  "setMix",      _setMix },
		{  "getMix",      _getMix },
		{  NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
// Ctor, Dtor
//----------------------------------------------------------------//
MOAISpineAnimationMixTable::MOAISpineAnimationMixTable()
{
	RTTI_BEGIN
		RTTI_SINGLE( MOAISpineAnimationMixTable )
	RTTI_END
}

MOAISpineAnimationMixTable::~MOAISpineAnimationMixTable() {
	MixMapIt it = this->mMixMap.begin ();
	for ( ; it != this->mMixMap.end (); ++it ) {
		MOAISpineAnimationMixEntry* entry = it->second;
		delete entry;
	}	
}

//----------------------------------------------------------------//
MOAISpineAnimationMixEntry* MOAISpineAnimationMixTable::AffirmMix( 
		STLString src,
		STLString target
	) {
	STLString key = src;
	key += "->";
	key += target;
	MixMapIt it = mMixMap.find( key );
	if( it == mMixMap.end() ) { //not found, create one
		MOAISpineAnimationMixEntry* entry = new MOAISpineAnimationMixEntry();
		mMixMap.insert( pair< STLString, MOAISpineAnimationMixEntry* > ( key, entry ) ) ;
		return entry;
	}
	return it->second;
}

//----------------------------------------------------------------//
MOAISpineAnimationMixEntry* MOAISpineAnimationMixTable::GetMix( 
		STLString src,
		STLString target
	) {
	STLString key = src;
	key += "->";
	key += target;
	MixMapIt it = mMixMap.find( key );
	if( it == mMixMap.end() ) return NULL;
	return it->second;
}

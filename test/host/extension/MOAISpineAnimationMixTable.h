#ifndef MOAISPINEANIMATIONMIXTABLE_H
#define MOAISPINEANIMATIONMIXTABLE_H
#include <moai-core/headers.h>

//----------------------------------------------------------------//
class MOAISpineAnimationMixEntry
{
public:
	STLString mSrc;
	STLString mTarget;
	// STLString mOverlay;
	float     mDuration;
	float     mDelay; //delay before playing target animation, should be < mDuration
};

//----------------------------------------------------------------//
class MOAISpineAnimationMixTable :
	public virtual MOAILuaObject
{
private:
	typedef STLMap < STLString, MOAISpineAnimationMixEntry* >::iterator MixMapIt;
	STLMap < STLString, MOAISpineAnimationMixEntry* > mMixMap ;

	static int _setMix       ( lua_State* L );
	static int _getMix       ( lua_State* L );

	MOAISpineAnimationMixEntry* AffirmMix( STLString src, STLString target );

public:

	MOAISpineAnimationMixEntry* GetMix( STLString src, STLString target );
	// void SetMix();

	DECL_LUA_FACTORY( MOAISpineAnimationMixTable )

	MOAISpineAnimationMixTable();
	~MOAISpineAnimationMixTable();

	void RegisterLuaClass ( MOAILuaState& state );
	void RegisterLuaFuncs ( MOAILuaState& state );

};
#endif
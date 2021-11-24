#ifndef	MOAISPINEANIMATION_H
#define	MOAISPINEANIMATION_H

#include <moai-core/pch.h>
#include <moai-core/MOAILogMessages.h>

#include <moai-sim/pch.h>
#include <moai-sim/MOAIProp.h>

#include <spine/spine.h>

#include "MOAISpineSkeleton.h"

#define MAX_SPINE_EVENT 64


class MOAISpineSkeleton;
class MOAISpineAnimation;
class MOAISpineAnimationTrack;
class MOAISpineAnimationMixTable;

//----------------------------------------------------------------//
class MOAISpineAnimationSpan :
	public virtual MOAILuaObject
{

	friend class MOAISpineAnimationTrack;
	friend class MOAISpineAnimation;

private:	
	
	static int _setMixDuration        ( lua_State* L );
	static int _getDuration           ( lua_State* L );

 	ZLLeanLink < MOAISpineAnimationSpan* > mLinkInTrack;
	Animation* mAnimation;
	float mTime, mDuration, mOffset, mEndTime;
	float mDelay;
	float mMixDuration;
	bool  mLoop;
	bool  mReversed;

public:

	MOAISpineAnimationSpan ();

	DECL_LUA_FACTORY( MOAISpineAnimationSpan )
	void    RegisterLuaClass		( MOAILuaState& state );
	void    RegisterLuaFuncs		( MOAILuaState& state );

};


//----------------------------------------------------------------//
class MOAISpineAnimationTrack :
	public virtual MOAILuaObject
{
	
	friend class MOAISpineAnimation;

private:
	
	static int _addSpan           ( lua_State* L );
	static int _removeSpan        ( lua_State* L );
	static int _clear             ( lua_State* L );

	typedef ZLLeanList < MOAISpineAnimationSpan* >::Iterator SpanIt;
 	ZLLeanLink < MOAISpineAnimationTrack* > mLinkInAnimation;
	ZLLeanList < MOAISpineAnimationSpan* > mSpans;
	MOAISpineAnimation *mParent; //TODO: gc problem?
	MOAISpineAnimationSpan* mPrevSpan;
	MOAISpineAnimationSpan* mMixingSpan;

	void    ApplyTime     ( float time );
	void    ApplyTime     ( float t0, float t1 );

	int     ApplySpan      ( MOAISpineAnimationSpan* span, float t0, float t1 );
	int     MixSpan        ( MOAISpineAnimationSpan* span, float t0, float t1, float alpha );

public:

	MOAISpineAnimationTrack  ();
	~MOAISpineAnimationTrack ();

	MOAISpineAnimationSpan*  AddSpan  ( float time, const char* name, bool loop, float offset, float duration, bool reversed );
	void    RemoveSpan                ( MOAISpineAnimationSpan* span );
	void    ClearSpans                ();

	DECL_LUA_FACTORY( MOAISpineAnimationTrack )
	void    RegisterLuaClass		( MOAILuaState& state );
	void    RegisterLuaFuncs		( MOAILuaState& state );

};

//----------------------------------------------------------------//
//Animation
//----------------------------------------------------------------//
class MOAISpineAnimation:
	public virtual MOAITimer
{
		friend class MOAISpineAnimationTrack;
	private:

		static int _init               ( lua_State* L );
		static int _addTrack           ( lua_State* L );
		static int _removeTrack        ( lua_State* L );
		static int _getTracks          ( lua_State* L );
		static int _setSkeleton        ( lua_State* L );
		static int _setMixTable        ( lua_State* L );
		static int _setBlending        ( lua_State* L );
		static int _apply              ( lua_State* L );

		typedef ZLLeanList < MOAISpineAnimationTrack* >::Iterator TrackIt;
		ZLLeanList < MOAISpineAnimationTrack* >     mTracks;

		MOAILuaSharedPtr < MOAISpineSkeletonData >	    mSkeletonData;
		MOAILuaSharedPtr < MOAISpineSkeletonBase >	    mSkeleton;
		MOAILuaSharedPtr < MOAISpineAnimationMixTable >	mMixTable;

		float   mLastTime;
		float   mBlendingFactor;

		Event** mSpineEvents;
		void ProcessEvents( MOAISpineAnimationTrack* track, int count );

	public:

		DECL_LUA_FACTORY( MOAISpineAnimation )

		enum {
			EVENT_SPINE_ANIMATION_START = MOAITimer::TOTAL_EVENTS,
			EVENT_SPINE_ANIMATION_END,
			EVENT_SPINE_ANIMATION_COMPLETE,
			EVENT_SPINE_ANIMATION_EVENT,
			TOTAL_EVENTS
		};

		MOAISpineAnimation();
		~MOAISpineAnimation();

		void    RegisterLuaClass		( MOAILuaState& state );
		void    RegisterLuaFuncs		( MOAILuaState& state );

		void    OnUpdate            ( float step );

		void    Init                ( MOAISpineSkeletonData* data );
		void    SetSkeleton         ( MOAISpineSkeletonBase* skeleton );
		void    SetMixTable         ( MOAISpineAnimationMixTable* mixTable );

		MOAISpineAnimationTrack*    AddTrack  ();
		void    RemoveTrack         ( MOAISpineAnimationTrack* track );
		void    ClearTracks         ();

		void    ApplyTime           ( float time );
		void    ApplyTime           ( float t0, float t1 );

		Animation*   FindAnimation  ( const char* name );

};

#endif

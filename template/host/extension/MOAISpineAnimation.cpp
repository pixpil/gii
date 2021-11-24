#include "MOAISpineAnimation.h"
#include "MOAISpineAnimationMixTable.h"

//----------------------------------------------------------------//
//Animation Track Span
//----------------------------------------------------------------//

int MOAISpineAnimationSpan::_getDuration ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimationSpan, "U" )
	state.Push( self->mDuration );	
	return 1;
}

int MOAISpineAnimationSpan::_setMixDuration ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimationSpan, "UN" )
	self->mMixDuration  = state.GetValue< float >( 2, -0.0f );
	return 0;
}

//Lua Registration
void	MOAISpineAnimationSpan::RegisterLuaClass	( MOAILuaState& state ){
	UNUSED( state )	;
}

void	MOAISpineAnimationSpan::RegisterLuaFuncs	( MOAILuaState& state ){
	luaL_Reg regTable [] = {
		{ "new",       MOAILogMessages::_alertNewIsUnsupported },
		{ "getDuration",      _getDuration },
		{ "setMixDuration",   _setMixDuration },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
MOAISpineAnimationSpan::MOAISpineAnimationSpan()
{
	RTTI_BEGIN
		RTTI_SINGLE ( MOAISpineAnimationSpan )
	RTTI_END
	mLinkInTrack.Data( this );

}



//----------------------------------------------------------------//
//Animation Track
//----------------------------------------------------------------//

int MOAISpineAnimationTrack::_addSpan ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimationTrack, "UNSB" )

	float time     = state.GetValue< float >( 2, 0 );
	cc8*  name     = lua_tostring( L, 3 );
	bool  loop     = state.GetValue< bool >( 4, false );
	float offset   = state.GetValue< float >( 5, 0.0f );
	float duration = state.GetValue< float >( 6, -1.0f );
	bool  reversed = state.GetValue< bool >( 7, false );

	MOAISpineAnimationSpan* span = self->AddSpan( time, name, loop, offset, duration, reversed );
	if( span ) {
		span->PushLuaUserdata( state );
		return 1;
	}
	return 0;
}


int MOAISpineAnimationTrack::_removeSpan ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimationTrack, "UU" )
	MOAISpineAnimationSpan* span = state.GetLuaObject < MOAISpineAnimationSpan >( 2, true );
	self->RemoveSpan( span );
	return 0;
}


int MOAISpineAnimationTrack::_clear ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimationTrack, "U" )
	self->ClearSpans();
	return 0;
}

//Lua Registration
void	MOAISpineAnimationTrack::RegisterLuaClass	( MOAILuaState& state ){
	UNUSED( state )	;
}

void	MOAISpineAnimationTrack::RegisterLuaFuncs	( MOAILuaState& state ){
	luaL_Reg regTable [] = {
		{ "new",            MOAILogMessages::_alertNewIsUnsupported },
		{ "addSpan",        _addSpan },
		{ "removeSpan",     _removeSpan },
		{ "clear",          _clear },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}

// Ctor, Dtor
MOAISpineAnimationTrack::MOAISpineAnimationTrack()
{
	RTTI_BEGIN
		RTTI_SINGLE( MOAISpineAnimationTrack )
	RTTI_END
	this->mLinkInAnimation.Data( this );
	mMixingSpan  = NULL;
	mPrevSpan    = NULL;
}

MOAISpineAnimationTrack::~MOAISpineAnimationTrack() {
	this->ClearSpans();
}

//----------------------------------------------------------------//
MOAISpineAnimationSpan* 
MOAISpineAnimationTrack::AddSpan( float time, const char* name, bool loop, float offset, float duration, bool reversed ) {
	Animation* anim = mParent->FindAnimation( name );
	if( !anim ) return NULL;
	MOAISpineAnimationSpan* span = new MOAISpineAnimationSpan();
	span->mTime            = time;
	span->mAnimation       = anim;
	span->mLoop            = loop;
	span->mOffset          = offset;
	span->mMixDuration     = 0.0f;
	span->mDelay           = 0.0f;
	span->mReversed        = reversed;

	if( duration<0 ) {
		span->mDuration = anim->duration - offset;
	} else {
		span->mDuration = duration;
	}

	span->mEndTime    = time + span->mDuration;	
	if( mSpans.Count() > 0 && mParent->mMixTable ){
		MOAISpineAnimationSpan* prevSpan = mSpans.Back();
		MOAISpineAnimationMixEntry* entry = mParent->mMixTable->GetMix( 
			prevSpan->mAnimation->name,
			span->mAnimation->name
		);
		if( entry ) {
			prevSpan->mMixDuration = entry->mDuration;
			span->mDelay           = entry->mDelay;
		}
	}
	this->mSpans.PushBack( span->mLinkInTrack );
	this->LuaRetain( span );

	return span;
}

//----------------------------------------------------------------//
void MOAISpineAnimationTrack::RemoveSpan( MOAISpineAnimationSpan* span ) {
	span->mLinkInTrack.Remove();
	this->LuaRelease( span );
}

//----------------------------------------------------------------//
void MOAISpineAnimationTrack::ClearSpans() {
	SpanIt spanIt = this->mSpans.Head ();
	while ( spanIt ) {
		MOAISpineAnimationSpan* span = spanIt->Data ();
		spanIt = spanIt->Next ();
		this->LuaRelease( span );
	}
	this->mSpans.Clear ();
}

//----------------------------------------------------------------//
//TODO: use binary search? ( there won't be too many spans anyway... )
void MOAISpineAnimationTrack::ApplyTime( float time ) {
	//find span
	MOAISpineSkeletonBase* Skeleton = this->mParent->mSkeleton;
	if( !Skeleton ) return;
	ApplyTime( -1.0, time );
}

void MOAISpineAnimationTrack::ApplyTime( float t0, float t1 ) {
	MOAISpineSkeletonBase* Skeleton = this->mParent->mSkeleton;
	if( !Skeleton ) return;

	SpanIt spanIt = this->mSpans.Head ();
	MOAISpineAnimationSpan* prevSpan = NULL;
	float alpha = 0.0f;

	MOAISpineAnimationSpan* spansToApply[ 8 ];
	float spanWeights[ 8 ];
	int spanCount = 0;
	float totalWeight = 0.0f;

	while ( spanIt ) { 
		//find spans within update timespan
		MOAISpineAnimationSpan* span = spanIt->Data ();
		spanIt = spanIt->Next ();

		if( t1 < span->mTime ) {
			//TODO: need sort the span by time
			continue; 
		}

		float endTimeMix = span->mEndTime + span->mMixDuration;
		
		if( t1 > endTimeMix ) {
			if( t0 >= 0 && t0 <= endTimeMix ) { //span is skipped, need to grab events out
				int eventCount = ApplySpan( span, t0, t1 );
				if( eventCount > 0 ) {
					mParent->ProcessEvents( this, eventCount );
				}
			}
			continue;
		}

		float weight = 0.0f;
		//t1>=span->mTime && t1 < span->mEndTime + mMixDuration
		if( span->mMixDuration > 0 ) {
			weight = 1 - ( t1 - span->mEndTime ) / span->mMixDuration ;
			if( weight > 1 ) weight = 1;
		} else {
			weight = 1.0f;
		}

		spansToApply [ spanCount ] = span;
		spanWeights  [ spanCount ] = weight;
		spanCount += 1;		
		totalWeight += weight;		
	}

	//perform animation
	for( int i = 0; i < spanCount; i++ ) {
		int	eventCount = 0;
		float alpha = ( i == 0 ? 1.0f : spanWeights[ i ] ) * mParent->mBlendingFactor;
		if( alpha >= .99f ) {
			eventCount = ApplySpan( spansToApply[i], t0, t1 );
		} else {
			eventCount = MixSpan( spansToApply[i], t0, t1, alpha );
		}
		if( eventCount > 0 && t0 >= 0.0f ) {
			mParent->ProcessEvents( this, eventCount );
		}
	}	
}

//----------------------------------------------------------------//
int MOAISpineAnimationTrack::ApplySpan( 
		MOAISpineAnimationSpan* span, float t0, float t1
	) {
	int eventCount = 0;
	MOAISpineSkeletonBase* skeleton = this->mParent->mSkeleton;
	if( !skeleton->mSkeleton ) return 0;
	if( !span->mReversed ) {
		Animation_apply(
			span->mAnimation,
			skeleton->mSkeleton,
			t0 - span->mTime + span->mOffset,
			t1 - span->mTime + span->mOffset,
			span->mLoop,
			mParent->mSpineEvents,
			&eventCount
		);
	} else {
		float duration = span->mAnimation->duration;
		Animation_apply(
			span->mAnimation,
			skeleton->mSkeleton,
			duration - ( t0 - span->mTime + span->mOffset ),
			duration - ( t1 - span->mTime + span->mOffset ), 
			span->mLoop,
			mParent->mSpineEvents,
			&eventCount
		);
	}
	return eventCount;
}

//----------------------------------------------------------------//
int MOAISpineAnimationTrack::MixSpan( 
		MOAISpineAnimationSpan* span, float t0, float t1, float alpha
	) {
	int eventCount = 0;
	MOAISpineSkeletonBase* Skeleton = this->mParent->mSkeleton;
	if( !Skeleton->mSkeleton ) return 0;
	if( !span->mReversed ) {
		Animation_mix(
			span->mAnimation,
			Skeleton->mSkeleton,
			t0 - span->mTime + span->mOffset,
			t1 - span->mTime + span->mOffset,
			span->mLoop,
			mParent->mSpineEvents,
			&eventCount,
			alpha
		);
	} else {
		float duration = span->mAnimation->duration;
		Animation_mix(
			span->mAnimation,
			Skeleton->mSkeleton,
			duration - ( t0 - span->mTime + span->mOffset ),
			duration - ( t1 - span->mTime + span->mOffset ),
			span->mLoop,
			mParent->mSpineEvents,
			&eventCount,
			alpha
		);
	}
	return eventCount;
}


//----------------------------------------------------------------//
//Animation
//----------------------------------------------------------------//

//Lua Glue
int MOAISpineAnimation::_init ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimation, "UU" )
	MOAISpineSkeletonData* data = state.GetLuaObject < MOAISpineSkeletonData >( 2, true );
	if( !data ) return 0;
	self->Init( data );
	return 0;
}

int MOAISpineAnimation::_setSkeleton ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimation, "UU" )
	MOAISpineSkeletonBase* skeleton = state.GetLuaObject < MOAISpineSkeletonBase >( 2, true );
	self->SetSkeleton( skeleton );
	return 0;		
}

int MOAISpineAnimation::_setMixTable ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimation, "UU" )
	MOAISpineAnimationMixTable* mixTable = 
		state.GetLuaObject < MOAISpineAnimationMixTable >( 2, true );
	self->SetMixTable( mixTable );
	return 0;		
}

int MOAISpineAnimation::_setBlending ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimation, "UN" )
	self->mBlendingFactor = state.GetValue< float >( 2, 1.0f );
	return 0;		
}

int MOAISpineAnimation::_addTrack ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimation, "U" )
	MOAISpineAnimationTrack* track = self->AddTrack();
	track->PushLuaUserdata( state );
	return 1;
}

int MOAISpineAnimation::_removeTrack ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimation, "UU" )
	MOAISpineAnimationTrack* track  = state.GetLuaObject < MOAISpineAnimationTrack >( 2, true );
	self->RemoveTrack( track );
	return 0;		
}


int MOAISpineAnimation::_getTracks ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimation, "U" )
	int count = 0;
	TrackIt trackIt = self->mTracks.Head ();
	while ( trackIt ) {
		MOAISpineAnimationTrack* track = trackIt->Data ();
		track->PushLuaUserdata( state );
		count++;
		trackIt = trackIt->Next ();
	}
	return count;
}

int MOAISpineAnimation::_apply ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineAnimation, "UN" )
	float time     = state.GetValue< float >( 2, 0.0f );
	self->ApplyTime( time );
	return 0;		
}


//Lua Registration
void	MOAISpineAnimation::RegisterLuaClass	( MOAILuaState& state ){
	MOAITimer::RegisterLuaClass( state );
	state.SetField ( -1, "EVENT_SPINE_ANIMATION_START",     ( u32 )EVENT_SPINE_ANIMATION_START    );
	state.SetField ( -1, "EVENT_SPINE_ANIMATION_END",       ( u32 )EVENT_SPINE_ANIMATION_END      );
	state.SetField ( -1, "EVENT_SPINE_ANIMATION_COMPLETE",  ( u32 )EVENT_SPINE_ANIMATION_COMPLETE );
	state.SetField ( -1, "EVENT_SPINE_ANIMATION_EVENT",     ( u32 )EVENT_SPINE_ANIMATION_EVENT    );
}

void	MOAISpineAnimation::RegisterLuaFuncs	( MOAILuaState& state ){
	MOAITimer::RegisterLuaFuncs( state );
	luaL_Reg regTable [] = {
		{ "init",          _init },
		{ "setSkeleton",   _setSkeleton },
		{ "setMixTable",   _setMixTable },
		{ "setBlending",   _setBlending },
		{ "addTrack",      _addTrack },
		{ "removeTrack",   _removeTrack },
		{ "getTracks",     _getTracks   },
		{ "apply",         _apply },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}

// Ctor, Dtor
MOAISpineAnimation::MOAISpineAnimation()
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAITimer )
	RTTI_END
	mSpineEvents = ( Event** ) malloc ( sizeof( Event* ) * MAX_SPINE_EVENT );
	mBlendingFactor = 1.0f;
}

MOAISpineAnimation::~MOAISpineAnimation() {
	this->ClearTracks();
	this->mMixTable.Set( *this, 0 );
	this->mSkeletonData.Set( *this, 0 );
	this->mSkeleton.Set( *this, 0 );
	free( mSpineEvents );
}

//----------------------------------------------------------------//
void MOAISpineAnimation::OnUpdate( float delta ) {
	MOAITimer::OnUpdate( delta );
	float time = this->GetTime();
	this->ApplyTime( this->mLastTime, time );
	this->mLastTime = time;
}

//----------------------------------------------------------------//
void MOAISpineAnimation::ApplyTime( float time ) {
	ApplyTime( -1.0f, time );	
}

//----------------------------------------------------------------//
void MOAISpineAnimation::ApplyTime( float t0, float t1 ) {
	if( mSkeleton ) {	mSkeleton->SetToSetupPose(); }
	TrackIt trackIt = this->mTracks.Head ();
	while ( trackIt ) {
		MOAISpineAnimationTrack* track = trackIt->Data ();
		trackIt = trackIt->Next ();
		track->ApplyTime( t0, t1 );
	}
	if( mSkeleton ) { mSkeleton->UpdateSpine(); }
}

//----------------------------------------------------------------//
void MOAISpineAnimation::Init( MOAISpineSkeletonData* skeletonData ) {
	mSkeletonData.Set( *this, skeletonData );
}

//----------------------------------------------------------------//
void MOAISpineAnimation::ProcessEvents( MOAISpineAnimationTrack* track, int eventCount ) {
	MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();
	for ( int ii = 0; ii < eventCount; ii++) {
		Event* event = mSpineEvents[ ii ];
		if ( this->PushListenerAndSelf ( EVENT_SPINE_ANIMATION_EVENT, state ) ) {
			track->PushLuaUserdata( state );
			lua_pushstring( state, event->data->name );
			state.Push( event->intValue );
			state.Push( event->floatValue );
			lua_pushstring( state, event->stringValue );
			state.DebugCall ( 6, 0 );
		}
		return;
	}
}

//----------------------------------------------------------------//
void MOAISpineAnimation::SetSkeleton( MOAISpineSkeletonBase* skeleton ) {
	mSkeleton.Set( *this, skeleton );	
}

//----------------------------------------------------------------//
void MOAISpineAnimation::SetMixTable( MOAISpineAnimationMixTable* mixTable ) {
	mMixTable.Set( *this, mixTable );	
}

//----------------------------------------------------------------//
MOAISpineAnimationTrack* MOAISpineAnimation::AddTrack() {
	MOAISpineAnimationTrack* track = new MOAISpineAnimationTrack();
	track->mParent = this;
	mTracks.PushBack( track->mLinkInAnimation );
	this->LuaRetain( track );
	return track;
}

//----------------------------------------------------------------//
void MOAISpineAnimation::RemoveTrack( MOAISpineAnimationTrack* track ) {
	track->mLinkInAnimation.Remove();
	this->LuaRelease( track );
}

//----------------------------------------------------------------//
void MOAISpineAnimation::ClearTracks() {
	// release all the shapes associated with this body
	TrackIt trackIt = this->mTracks.Head ();
	while ( trackIt ) {
		MOAISpineAnimationTrack* track = trackIt->Data ();
		trackIt = trackIt->Next ();
		this->LuaRelease ( track );
	}
	this->mTracks.Clear ();
}

//----------------------------------------------------------------//
Animation*  MOAISpineAnimation::FindAnimation( const char* name ) {
	if( !this->mSkeletonData ) return NULL;
	return this->mSkeletonData->FindAnimation( name );
}

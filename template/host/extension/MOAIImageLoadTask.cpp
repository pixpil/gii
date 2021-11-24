#include "MOAIImageLoadTask.h"
#include "moai-util/MOAITaskSubscriber.h"

//================================================================//
// MOAIImageLoadTask
//================================================================//

int MOAIImageLoadTask::_start ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAIImageLoadTask, "UUS" )

	MOAITaskQueue* queue	= state.GetLuaObject < MOAITaskQueue >( 2, true );
	cc8* filename = state.GetValue < cc8* >( 3, "" );
	u32 transform = state.GetValue < u32 >( 4, 0 );
	
	self->mFilename  = filename;
	self->mTransform = transform;
	if( state.IsType( 5, LUA_TFUNCTION ) ) {
		self->mOnFinish.SetRef ( *self, state, 5 );
	}
	MOAIImage *img = new MOAIImage();
	self->mImage.Set( *self, img );
	self->Start ( *queue, MOAIMainThreadTaskSubscriber::Get() );
	return 0;
}

//----------------------------------------------------------------//
void MOAIImageLoadTask::Execute () {
	// printf( "loading image %s\n", this->mFilename.c_str() );
	this->mImage->Load ( this->mFilename, this->mTransform );	
	// printf( "loading image done %s\n", this->mFilename.c_str() );
}

//----------------------------------------------------------------//
MOAIImageLoadTask::MOAIImageLoadTask () :
	mTransform( 0 )
{
	RTTI_SINGLE ( MOAITask )
}

//----------------------------------------------------------------//
MOAIImageLoadTask::~MOAIImageLoadTask () {
	this->mImage.Set ( *this, 0 );
}

//----------------------------------------------------------------//
void MOAIImageLoadTask::Publish () {
	if ( this->mOnFinish ) {
		MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();
		if ( this->mOnFinish.PushRef ( state )) {
			this->mImage->PushLuaUserdata ( state );
			state.DebugCall ( 1, 0 );
		}
	}
}

//----------------------------------------------------------------//
void MOAIImageLoadTask::RegisterLuaClass ( MOAILuaState& state ) {
	UNUSED( state );
}

//----------------------------------------------------------------//
void MOAIImageLoadTask::RegisterLuaFuncs ( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		{ "start",		_start },
		{ NULL, NULL }
	};
	luaL_register ( state, 0, regTable );
}

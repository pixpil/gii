#include "MOAISpineSkeletonData.h"
//----------------------------------------------------------------//
//Lua Glue
//----------------------------------------------------------------//
int MOAISpineSkeletonData::_load ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "USS" )
	cc8* skelFile  = lua_tostring( L, 2 );
	cc8* atlasFile = lua_tostring( L, 3 );
	state.Push( self->Load( skelFile, atlasFile ) );
	return 1;
}

int MOAISpineSkeletonData::_loadWithAtlas ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "USU" )
	cc8* skelFile  = lua_tostring( L, 2 );
	MOAISpineAtlas* atlas = state.GetLuaObject< MOAISpineAtlas >( 3, true );
	state.Push( self->LoadWithAtlas( skelFile, atlas->mAtlas ) );
	//todo: lua_retain?
	return 1;
}

int MOAISpineSkeletonData::_loadFromString ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "USS" )
	cc8* skelFile  = lua_tostring( L, 2 );
	cc8* atlasFile = lua_tostring( L, 3 );
	// state.Push( self->Load( skelFile, atlasFile ) );
	state.Push( false );
	return 1;
}

int MOAISpineSkeletonData::_getAnimationNames ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "U" )
	if( !self->mData ) return 0;
	u32 count = self->mData->animationCount;
	lua_newtable( state );
	for( u32 i = 0; i < count; ++ i ) {
		Animation* ani = self->mData->animations[ i ];
		lua_pushstring( state, ani->name );
		lua_pushnumber( state, i );
		lua_settable( state, -3 );
	}
	return 1;
}

int MOAISpineSkeletonData::_getSkinNames ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "U" )
	if( !self->mData ) return 0;
	u32 count = self->mData->skinCount;
	lua_newtable( state );
	for( u32 i = 0; i < count; ++ i ) {
		Skin* skin = self->mData->skins[ i ];
		lua_pushstring( state, skin->name );
		lua_pushnumber( state, i );
		lua_settable( state, -3 );
	}
	return 1;
}


int MOAISpineSkeletonData::_getBoneNames ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "U" )
	if( !self->mData ) return 0;
	u32 count = self->mData->boneCount;
	lua_newtable( state );
	for( u32 i = 0; i < count; ++ i ) {
		BoneData* bone = self->mData->bones[ i ];
		lua_pushstring( state, bone->name );
		lua_pushnumber( state, i );
		lua_settable( state, -3 );
	}
	return 1;
}

int MOAISpineSkeletonData::_getSlotNames ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "U" )
	if( !self->mData ) return 0;
	u32 count = self->mData->slotCount;
	lua_newtable( state );
	for( u32 i = 0; i < count; ++ i ) {
		SlotData* slot = self->mData->slots[ i ];
		lua_pushstring( state, slot->name );
		lua_pushnumber( state, i );
		lua_settable( state, -3 );
	}
	return 1;
}

int MOAISpineSkeletonData::_getEventNames ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "U" )
	if( !self->mData ) return 0;
	u32 count = self->mData->eventCount;
	lua_newtable( state );
	for( u32 i = 0; i < count; ++ i ) {
		EventData* ev = self->mData->events[ i ];
		lua_pushstring( state, ev->name );
		lua_pushnumber( state, i );
		lua_settable( state, -3 );
	}
	return 1;
}

int MOAISpineSkeletonData::_getAnimationDuration ( lua_State *L ) {
	MOAI_LUA_SETUP( MOAISpineSkeletonData, "US" )
	if( !self->mData ) return 0;
	cc8* aniName = lua_tostring( L, 2 );
	Animation* ani = SkeletonData_findAnimation( self->mData, aniName );
	if( ani ) {
		state.Push( ani->duration );
		return 1;
	}
	return 0;
}

//----------------------------------------------------------------//
//Lua Registration
//----------------------------------------------------------------//
void	MOAISpineSkeletonData::RegisterLuaClass	( MOAILuaState& state ){
	UNUSED( state );
}

void	MOAISpineSkeletonData::RegisterLuaFuncs	( MOAILuaState& state ){
	luaL_Reg regTable [] = {
		{ "load",                  _load                 },
		{ "loadWithAtlas",         _loadWithAtlas        },
		{ "loadFromString",        _loadFromString       },
		{ "getAnimationNames",     _getAnimationNames    },
		{ "getSkinNames",          _getSkinNames         },
		{ "getBoneNames",          _getBoneNames         },
		{ "getSlotNames",          _getSlotNames         },
		{ "getEventNames",         _getEventNames        },
		{ "getAnimationDuration",  _getAnimationDuration },
		{  NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
// Ctor, Dtor
//----------------------------------------------------------------//
MOAISpineSkeletonData::MOAISpineSkeletonData()
: mData( NULL ), mAtlas( NULL )
{
	RTTI_BEGIN
		RTTI_SINGLE( MOAISpineSkeletonData )
	RTTI_END
}

MOAISpineSkeletonData::~MOAISpineSkeletonData() {
	if( mData ) SkeletonData_dispose( mData );
	// if( mAtlas ) Atlas_dispose( mAtlas );
	DeckMapIt deckMapIt = this->mAttachmentDeckMap.begin ();
	for ( ; deckMapIt != this->mAttachmentDeckMap.end (); ++deckMapIt ) {
		MOAIDeck* deck = deckMapIt->second;
		deck->Release();
	}
}


//----------------------------------------------------------------//
bool MOAISpineSkeletonData::Load( const char* skelFile, const char* atlasFile ) {
	mAtlas = Atlas_createFromFile( atlasFile, 0 ) ;
	return LoadWithAtlas( skelFile, mAtlas );
}

//----------------------------------------------------------------//
bool MOAISpineSkeletonData::LoadWithAtlas( const char* skelFile, Atlas* atlas ) {
	assert ( atlas );
	SkeletonJson* json = SkeletonJson_create( atlas );
	json->scale = 1.0f;
	mData = SkeletonJson_readSkeletonDataFile( json, skelFile );	
	SkeletonJson_dispose( json );
	if( !mData ) return false;
	return true;
}

//----------------------------------------------------------------//
Animation* MOAISpineSkeletonData::FindAnimation( const char* name ) {
	if( !this->mData ) return NULL;
	Animation* animation = 
		SkeletonData_findAnimation( this->mData, name );
	return animation;
}

//----------------------------------------------------------------//
//Tool Functions
//----------------------------------------------------------------//

int AtlasFilterToGL( AtlasFilter filter ) {
	switch( filter ) {
		case ATLAS_NEAREST:
			return ZGL_SAMPLE_LINEAR;
		case ATLAS_LINEAR:
			return ZGL_SAMPLE_LINEAR;
		case ATLAS_MIPMAP:
			return ZGL_SAMPLE_LINEAR_MIPMAP_LINEAR;
		case ATLAS_MIPMAP_NEAREST_NEAREST:
			return ZGL_SAMPLE_NEAREST_MIPMAP_NEAREST;
		case ATLAS_MIPMAP_LINEAR_NEAREST:
			return ZGL_SAMPLE_LINEAR_MIPMAP_NEAREST;
		case ATLAS_MIPMAP_NEAREST_LINEAR:
			return ZGL_SAMPLE_NEAREST_MIPMAP_LINEAR;
		case ATLAS_MIPMAP_LINEAR_LINEAR:
			return ZGL_SAMPLE_LINEAR_MIPMAP_LINEAR;
	}
	return ZGL_SAMPLE_LINEAR;
}

void _AtlasPage_createTexture (AtlasPage* self, const char* path) {
	MOAITexture* texture = new MOAITexture();
	texture->Init( path, MOAIImageTransform::TRUECOLOR ) ;//| MOAIImageTransform::PREMULTIPLY_ALPHA );
	texture->SetFilter( 
			AtlasFilterToGL( self->minFilter ), AtlasFilterToGL( self->magFilter )
		);
	self->rendererObject = texture;
	self->width  = texture->GetWidth();
	self->height = texture->GetHeight();
}

void _AtlasPage_disposeTexture (AtlasPage* self) {
	// delete ( (MOAITexture*)self->rendererObject );
}

char* _Util_readFile (const char* path, int* length) {
	ZLFileStream stream;
	if ( !stream.OpenRead ( path )) {
		length = 0;
		return NULL;
	}

	STLString absFilePath = ZLFileSys::GetAbsoluteFilePath ( path );
	STLString absDirPath = ZLFileSys::TruncateFilename ( absFilePath );

	u32 len = stream.GetLength ();
	char* buf = ( char* )malloc ( len + 1 );
	stream.ReadBytes ( buf, len );
	buf [ len ] = '\0';
	stream.Close ();
	*length = len;
	return buf;
	
}

#include "MOAISpineAtlas.h"

int MOAISpineAtlas::_addRegion ( lua_State* L ) {
	MOAI_LUA_SETUP( MOAISpineAtlas, "USU" )
	cc8* name;
	MOAITexture *texture;
	float tw, th;
	float width, height;
	float originalWidth, originalHeight;
	float x, y;
	float offsetX, offsetY;
	int index;
	bool rotated;
	
	AtlasRegion *region;

	name           = lua_tostring( state, 2 );
	texture        = state.GetLuaObject< MOAITexture >( 3, true );

	width          = state.GetValue< float >( 4, 0 );
	height         = state.GetValue< float >( 5, 0 );
	
	originalWidth  = state.GetValue< float >( 6, 0 );
	originalHeight = state.GetValue< float >( 7, 0 );

	offsetX        = state.GetValue< float >( 8, 0 );
	offsetY        = state.GetValue< float >( 9, 0 );

	x              = state.GetValue< float >( 10, 0 );
	y              = state.GetValue< float >( 11, 0 );

	index          = state.GetValue< int  >( 12, -1 );
	rotated        = state.GetValue< bool >( 13, 0 );


	tw = state.GetValue< float >( 14, (float)texture->GetWidth() );
	th = state.GetValue< float >( 15, (float)texture->GetHeight() );

	region = AtlasRegion_create();
	if( self->mLastRegion ) 
		self->mLastRegion->next = region;
	else
		self->mAtlas->regions = region;

	self->mLastRegion = region;
	region->page = NULL;
	MALLOC_STR( region->name, name );
	region->rendererObject = (void*)texture;

	region->width     = width;
	region->height    = height;
	region->originalWidth  = originalWidth;
	region->originalHeight = originalHeight;
	region->offsetX   = offsetX;
	region->offsetY   = offsetY;
	region->x         = x;
	region->y         = y;
	region->rotate    = rotated;
	region->index     = index;
	region->u = region->x / tw;
	region->v = region->y / th;
	if (region->rotate) {
		region->u2 = (region->x + region->height) / tw;
		region->v2 = (region->y + region->width) / th;
	} else {
		region->u2 = (region->x + region->width) / tw;
		region->v2 = (region->y + region->height) / th;
	}
	// printf("%f,%f,%f,%f\n", region->u, region->v, region->u2, region->v2 );
	state.Push( true );
	return 1;
}


MOAISpineAtlas::MOAISpineAtlas () {
	RTTI_BEGIN
		RTTI_SINGLE( MOAISpineAtlas )
	RTTI_END
	mAtlas = NEW( Atlas );
	mAtlas->regions = 0;
	mAtlas->pages   = 0;
	mLastRegion   = NULL;
}

MOAISpineAtlas::~MOAISpineAtlas () {
	FREE( mAtlas );
}


void	MOAISpineAtlas::RegisterLuaClass	( MOAILuaState& state ){
	UNUSED( state );
}

void	MOAISpineAtlas::RegisterLuaFuncs	( MOAILuaState& state ){	
	luaL_Reg regTable [] = {
		{ "addRegion",       _addRegion   },		
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}


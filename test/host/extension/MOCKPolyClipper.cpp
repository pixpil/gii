#include "MOCKPolyClipper.h"

//----------------------------------------------------------------//
int MOCKPolyClipper::_executeOffset ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyClipper, "UTN" )
	float offset = state.GetValue < float >( 3, 1.0f );

	Paths pathsSubj;
	if( !self->GetPaths( state, 2, pathsSubj ) ) return 0;

	ClipperOffset clipperOffset;
	Paths solution;
	clipperOffset.AddPaths( pathsSubj, jtMiter, etClosedPolygon );
	// clipperOffset.AddPaths( pathsSubj, jtSquare, etClosedPolygon );
	clipperOffset.Execute( solution, offset * self->mUnitScale );

	return self->PushPaths( L, solution );
}

//----------------------------------------------------------------//
int MOCKPolyClipper::_executeBoolean ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyClipper, "UTTN" )
	u32 op = state.GetValue < u32 >( 4, CLIP_TYPE_UNION );
	Paths pathsSubj;
	Paths pathsClip;
	self->GetPaths( state, 2, pathsSubj );
	self->GetPaths( state, 3, pathsClip );

	Clipper clipper;
	clipper.AddPaths( pathsSubj, ptSubject, true );
	clipper.AddPaths( pathsClip, ptClip, true );

	Paths solution;
	clipper.Execute( ( ClipType )op, solution, pftNonZero, pftNonZero );

	return self->PushPaths( L, solution );
}

//----------------------------------------------------------------//
int MOCKPolyClipper::_simplifyPolygons ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyClipper, "UT" )
	Paths pathsSubj;
	if( !self->GetPaths( state, 2, pathsSubj ) ) return 0;
	Paths solution;
	SimplifyPolygons( pathsSubj, solution );

	return self->PushPaths( L, solution );
}

//----------------------------------------------------------------//
int MOCKPolyClipper::_cleanPolygons ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyClipper, "UTN" )
	float distance = state.GetValue < float >( 3, 1.0f );

	Paths pathsSubj;
	if( !self->GetPaths( state, 2, pathsSubj ) ) return 0;
	// Paths solution;
	CleanPolygons( pathsSubj, distance * self->mUnitScale );

	return self->PushPaths( L, pathsSubj );
}

//----------------------------------------------------------------//
int MOCKPolyClipper::_setUnitScale ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyClipper, "UN" )
	float scale = state.GetValue < float >( 2, 1.0f );
	if( scale <= 0.0f ) return 0;
	self->mUnitScale = scale;
	return 0;
}


//----------------------------------------------------------------//
int MOCKPolyClipper::PushPaths( lua_State* L, const Paths &paths ) {
	MOAILuaState state ( L );
	int count = paths.size();
	if( count <= 0 ) return 0;
	lua_createtable( L, count, 0 );
	for( int i = 0; i < count; ++i ) {
		MOCKPolyPath* polyPath = new MOCKPolyPath();
		polyPath->InitFromClipperPath( this->mUnitScale, paths[ i ] );
		polyPath->PushLuaUserdata( state ); //value
		lua_rawseti( L, -2, i + 1 );
	}
	return 1;
}


//----------------------------------------------------------------//
int MOCKPolyClipper::GetPaths( lua_State* L, int idx, Paths &output ) {
	MOAILuaState state ( L );
	u32 top = state.GetTop();
	u32 size = lua_objlen( L, idx );
	if ( size == 0 ) return 0;

	u32 count = 0;
	output.resize( size );

	lua_pushnil ( L ); //initial key
  while ( lua_next ( L, idx ) != 0 ) {
  	MOCKPolyPath* polyPath = state.GetLuaObject < MOCKPolyPath >( -1, 0 );
  	if ( !polyPath ) {
  		lua_pop ( L, 2 ); //invalid input, stop iteration
  		return 0;
  	}
  	Path path;
  	polyPath->GetClipperPath( this->mUnitScale, path );
  	output.push_back( path );
		lua_pop ( L, 1 ); //key stay
		count++;
	}

	return count;
}

//----------------------------------------------------------------//
MOCKPolyClipper::MOCKPolyClipper ()
	:mUnitScale( 10.0f )
{
	RTTI_BEGIN
		RTTI_SINGLE( MOCKPolyClipper )
	RTTI_END
}

MOCKPolyClipper::~MOCKPolyClipper () {
}

//----------------------------------------------------------------//
void MOCKPolyClipper::RegisterLuaClass ( MOAILuaState& state ) {
	state.SetField ( -1, "CLIP_TYPE_UNION",        ( u32 )CLIP_TYPE_UNION        );
	state.SetField ( -1, "CLIP_TYPE_INTERSECTION", ( u32 )CLIP_TYPE_INTERSECTION );
	state.SetField ( -1, "CLIP_TYPE_DIFFERENCE",   ( u32 )CLIP_TYPE_DIFFERENCE   );
	state.SetField ( -1, "CLIP_TYPE_XOR",          ( u32 )CLIP_TYPE_XOR          );
}

void MOCKPolyClipper::RegisterLuaFuncs ( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		{ "cleanPolygons",	    _cleanPolygons    },
		{ "executeOffset",	    _executeOffset    },
		{ "executeBoolean",	    _executeBoolean   },
		{ "setUnitScale", 	    _setUnitScale     },
		{ "simplifyPolygons", 	_simplifyPolygons },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

#include "MOCKPolyPartition.h"
#include "polypartition.h"

//----------------------------------------------------------------//
int MOCKPolyPartition::_doConvexPartition ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPartition, "UT" )
	list< TPPLPoly > polys, polysNoHole, result;
	if( !self->GetPolyList( state, 2, polys ) ) return 0;
	TPPLPartition pp;
	pp.RemoveHoles( &polys, &polysNoHole );
	// pp.ConvexPartition_OPT( &polysNoHole, &result );
	pp.ConvexPartition_HM( &polysNoHole, &result );
	return self->PushPolyList( L, result );
}

//----------------------------------------------------------------//
int MOCKPolyPartition::_doTriagulation ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKPolyPartition, "UT" )
	list< TPPLPoly > polys, result;
	if( !self->GetPolyList( state, 2, polys ) ) return 0;
	TPPLPartition pp;
	pp.Triangulate_EC( &polys, &result );
	// pp.ConvexPartition_HM( &polys, &result );
	return self->PushPolyList( L, result );
}


//----------------------------------------------------------------//
int MOCKPolyPartition::PushPolyList( lua_State* L, list< TPPLPoly > &polys ) {
	MOAILuaState state ( L );
	int count = polys.size();
	if( count <= 0 ) return 0;
	lua_createtable( L, count, 0 );
	
	list<TPPLPoly>::iterator iter;
	int i = 0;
	for(iter = polys.begin(); iter != polys.end(); iter++) {
		i++ ;
		MOCKPolyPath* polyPath = new MOCKPolyPath();
		polyPath->InitFromTPPLPoly( *iter );
		polyPath->PushLuaUserdata( state ); //value
		lua_rawseti( L, -2, i );		
	}
	for( int i = 0; i < count; ++i ) {
		
	}
	return 1;
}


//----------------------------------------------------------------//
int MOCKPolyPartition::GetPolyList( lua_State* L, int idx, list<TPPLPoly> &polys ) {
	MOAILuaState state ( L );
	u32 top = state.GetTop();
	u32 size = lua_objlen( L, idx );
	if ( size == 0 ) return 0;

	u32 count = 0;
	
	lua_pushnil ( L ); //initial key
  while ( lua_next ( L, idx ) != 0 ) {
  	MOCKPolyPath* polyPath = state.GetLuaObject < MOCKPolyPath >( -1, 0 );
  	if ( !polyPath ) {
  		lua_pop ( L, 2 ); //invalid input, stop iteration
  		return 0;
  	}
  	TPPLPoly poly;
  	polyPath->GetTPPLPoly( poly );
  	polys.push_back( poly );
		lua_pop ( L, 1 ); //key stay
		count++;
	}

	return count;
}

//----------------------------------------------------------------//
MOCKPolyPartition::MOCKPolyPartition ()
{
	RTTI_BEGIN
		RTTI_SINGLE( MOCKPolyPartition )
	RTTI_END
}

MOCKPolyPartition::~MOCKPolyPartition () {
}

//----------------------------------------------------------------//
void MOCKPolyPartition::RegisterLuaClass ( MOAILuaState& state ) {
	UNUSED( state );
}

void MOCKPolyPartition::RegisterLuaFuncs ( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		{ "doConvexPartition",	    _doConvexPartition    },
		{ "doTriagulation",	        _doTriagulation       },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}


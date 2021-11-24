
#include <TMInfluenceMap.h>

//----------------------------------------------------------------//
//MAP
//----------------------------------------------------------------//

int TMInfluenceMap::_init ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMap, "UNN" );
	u32   w               = state.GetValue< u32 >  ( 2, 0 );
	u32   h               = state.GetValue< u32 >  ( 3, 0 );
	u32   decayType       = state.GetValue< u32 >  ( 4, DECAY_LINEAR );
	float decayRate       = state.GetValue< float >( 5, 0.5 );
	float diffusionRate   = state.GetValue< float >( 6, 0.8 );
	self->init( w, h, decayType, decayRate, diffusionRate / 8.0 );
	return 0;
}

int TMInfluenceMap::_clearMap ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMap, "U" );
	self->clearMap();
	return 0;
}

int TMInfluenceMap::_getCell ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMap, "UNN" );
	u32   x = state.GetValue< u32 >( 2, 1 ) - 1 ;
	u32   y = state.GetValue< u32 >( 3, 1 ) - 1 ;
	float tile = self->getCell( x, y );
	state.Push( tile );
	return 1;
}

int TMInfluenceMap::_setCell ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMap, "UNNN" );
	u32   x    = state.GetValue< u32 >( 2, 1 ) - 1 ;
	u32   y    = state.GetValue< u32 >( 3, 1 ) - 1 ;
	float tile = state.GetValue< float >( 4, 0 );
	self->setCell( x, y, tile );
	return 0;
}

int TMInfluenceMap::_addCell ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMap, "UNNN" );
	u32   x    = state.GetValue< u32 >( 2, 1 ) - 1 ;
	u32   y    = state.GetValue< u32 >( 3, 1 ) - 1 ;
	float tile = state.GetValue< float >( 4, 0 );
	self->addCell( x, y, tile );
	return 0;
}


int TMInfluenceMap::_update ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMap, "U" );
	u32 iteration = state.GetValue< u32 >( 2, 0 );
	self->updateDiffusion( iteration );
	return 0;
}

//----------------------------------------------------------------//
TMInfluenceMap::TMInfluenceMap ():
	mWidth( 0 ),
	mHeight( 0 ),
	mDecayType( DECAY_LINEAR ),
	mDecayRate( 0.7 ),
	mCurrentMapId( 0 ),
	mDiffusionRate( 0.6 )
{
	RTTI_BEGIN
		RTTI_SINGLE( TMInfluenceMap )
	RTTI_END
}

//----------------------------------------------------------------//
TMInfluenceMap::~TMInfluenceMap () {
}

//----------------------------------------------------------------//
void TMInfluenceMap::init ( u32 width, u32 height, u32 decayType, float decayRate, float diffusionRate ) {
	mWidth  = width;
	mHeight = height;
	
	u32 count = width * height;

	mMap0      .Init( count );
#if INFLUENCEMAP_USE_DOUBLE_BUFFER
	mMap1      .Init( count );
#endif

	clearMap();

	mDecayType     = decayType;
	mDecayRate     = decayRate;
	mDiffusionRate = diffusionRate;

}

void TMInfluenceMap::clearMap () {
	mMap0.Fill( 0 );
#if INFLUENCEMAP_USE_DOUBLE_BUFFER
	mMap1.Fill( 0 );
#endif
}

#define DIAGONAL_DISTANCE 1.414f

#define GET_CELL( map, x, y )    (*map)[ (y) * mWidth + (x) ] 

#define SET_CELL( map, x, y, v )  (*map)[ (y) * mWidth + (x) ] = v

//----------------------------------------------------------------//
void TMInfluenceMap::updateDiffusion ( u32 iteration ){
	UNUSED( iteration );	
	ZLLeanArray< float > *mapRead;
	ZLLeanArray< float > *mapWrite;
#if INFLUENCEMAP_USE_DOUBLE_BUFFER
	if( mCurrentMapId == 0 ){ 
		mapRead  = &mMap0;
		mapWrite = &mMap1;
		mCurrentMapId = 1;
	}else{ 
		mapRead  = &mMap1;
		mapWrite = &mMap0;
		mCurrentMapId = 0;
	}
#else
	mapRead = &mMap0;
	mapWrite = &mMap0;
#endif

	//we don't update diffusion of edge. to save some code & overhead of boundary checking
	// if( mDecayType == DECAY_LINEAR ) {
		//horizontal pass
		for( u32 y = 1; y < mHeight - 1; y++ )
		for( u32 x = 1; x < mWidth  - 1; x++ ){
			//inital
			float value = 0.0f ;
			value += GET_CELL( mapRead, x, y) * 4.0f ;			
			//cross
			value += GET_CELL( mapRead, x,   y-1 ) ;
			value += GET_CELL( mapRead, x,   y+1 ) ;
			value += GET_CELL( mapRead, x-1, y   ) ;
			value += GET_CELL( mapRead, x+1, y   ) ;
			//diagonal
			// value += GET_CELL( mapRead, x-1, y-1 ) ;
			// value += GET_CELL( mapRead, x-1, y+1 ) ;
			// value += GET_CELL( mapRead, x+1, y-1 ) ;
			// value += GET_CELL( mapRead, x+1, y+1 ) ;
			value /= 4.0f + 4.0f;
			SET_CELL( mapWrite, x, y, value * mDecayRate );
		}
	// }
	// else { //DECAY_EXPONENTIAL
	// 	
	// }
}

//----------------------------------------------------------------//
float TMInfluenceMap::getCell ( u32 x, u32 y ) {
	return GET_CELL( getCurrentMap() , x, y );
}

void TMInfluenceMap::setCell ( u32 x, u32 y, float value) {
	SET_CELL( getCurrentMap() , x, y, value );
}

void TMInfluenceMap::addCell ( u32 x, u32 y, float value) {
	ZLLeanArray< float > * map = getCurrentMap();
	float ovalue = GET_CELL( map, x, y );
	SET_CELL( map, x, y, value + ovalue );
}


//----------------------------------------------------------------//
void TMInfluenceMap::RegisterLuaClass ( MOAILuaState& state ) {
	// UNUSED( state );
	state.SetField( -1, "DECAY_LINEAR",      ( u32 ) DECAY_LINEAR );
	state.SetField( -1, "DECAY_EXPONENTIAL", ( u32 ) DECAY_EXPONENTIAL );
}


void TMInfluenceMap::RegisterLuaFuncs ( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		{ "init",          _init },
		{ "clearMap",      _clearMap },
		{ "update",        _update },
		{ "getCell",       _getCell },
		{ "setCell",       _setCell },
		{ "addCell",       _addCell },
		{ NULL, NULL }
	};

	luaL_register( state, 0, regTable );
}


//----------------------------------------------------------------//
//WALKER
//----------------------------------------------------------------//
int TMInfluenceMapWalker::_reserve ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMapWalker, "UN" );
	u32 count = state.GetValue < u32 > ( 2, 0 );
	self->reserve ( count );
	return 0;
}

//----------------------------------------------------------------//
int TMInfluenceMapWalker::_setMap ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMapWalker, "UNU" );
	u32 id              = state.GetValue< u32 >( 2, 1 ) - 1;
	TMInfluenceMap* map = state.GetLuaObject< TMInfluenceMap >( 3, true );
	float weight        = state.GetValue< float >( 4, 1 );
	float offset        = state.GetValue< float >( 5, 0 );
	float multiplier    = state.GetValue< float >( 6, 1 );
	self->setMap( id, map, weight, offset, multiplier );
	return 0;
}

//----------------------------------------------------------------//
int TMInfluenceMapWalker::_updateStep ( lua_State *L ) {
	//todo
	MOAI_LUA_SETUP ( TMInfluenceMapWalker, "U" );
	self->updateStep( );
	return 0;
}

//----------------------------------------------------------------//
int TMInfluenceMapWalker::_getLoc ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMapWalker, "U" );
	state.Push( self->mX + 1 );
	state.Push( self->mY + 1 );
	return 2;
}

int TMInfluenceMapWalker::_setLoc ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMapWalker, "UNN" );
	u32 x = state.GetValue< u32 >( 2, 1 ) - 1 ;
	u32 y = state.GetValue< u32 >( 3, 1 ) - 1 ;
	self->mX = x;
	self->mY = y;
	return 0;
}

int TMInfluenceMapWalker::_addLoc ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMapWalker, "UNN" );
	u32 dx = state.GetValue< u32 >( 2, 0 );
	u32 dy = state.GetValue< u32 >( 3, 0 );
	self->mX += dx;
	self->mY += dy;
	return 0;
}

//----------------------------------------------------------------//
int TMInfluenceMapWalker::_calcScore ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMapWalker, "UNN" );
	u32 x = state.GetValue< u32 >( 2, 1 ) - 1 ;
	u32 y = state.GetValue< u32 >( 3, 1 ) - 1 ;
	state.Push( self->calcScore( x, y ) );
	return 1;
}

int TMInfluenceMapWalker::_getVector ( lua_State *L ) {
	MOAI_LUA_SETUP ( TMInfluenceMapWalker, "UNN" );
	u32 x = state.GetValue< u32 >( 2, 1 ) - 1 ;
	u32 y = state.GetValue< u32 >( 3, 1 ) - 1 ;
	ZLIntVec2D vec = self->getVector( x, y );
	state.Push( vec.mX );
	state.Push( vec.mY );
	return 2;
}


//----------------------------------------------------------------//
TMInfluenceMapWalker::TMInfluenceMapWalker():
	mX(0), mY(0),
	mDx(0), mDy(0)
{
	RTTI_BEGIN
		RTTI_SINGLE( TMInfluenceMapWalker )
	RTTI_END
}

TMInfluenceMapWalker::~TMInfluenceMapWalker(){
	for ( u32 i = 0; i < mConfigs.Size (); ++i ) {
		TMInfluenceMapWalkerConfig& config = mConfigs [ i ];
		config.mMap.Set ( *this, 0 );
	}
	mConfigs.Clear();
}


//----------------------------------------------------------------//
void TMInfluenceMapWalker::reserve ( u32 count ) {
	this->mConfigs.Init( count );
}

//----------------------------------------------------------------//
void TMInfluenceMapWalker::setMap ( u32 id, TMInfluenceMap* map, 
				float weight, float offset, float multiplier) {
	TMInfluenceMapWalkerConfig &config = this->mConfigs[id];
	config.mWeight     = weight;
	config.mOffset     = offset;
	config.mMultiplier = multiplier;
	config.mMap.Set( *this, map );
}

float TMInfluenceMapWalker::calcScore ( u32 x, u32 y ) {
	//score = weight/totalWeight * ( input + offset ) * multiplier
	float score = 0;
	float totalWeight = 0;
	for ( u32 i = 0; i < mConfigs.Size (); ++i ) {
		TMInfluenceMapWalkerConfig& config = mConfigs [ i ];
		TMInfluenceMap *map = config.mMap;
		totalWeight += config.mWeight;
		float input = map->getCell( x, y );
		score += config.mWeight * ( input + config.mOffset ) * config.mMultiplier;
	}
	if ( totalWeight == 0 ) return 0;
	return score / totalWeight;
}

void TMInfluenceMapWalker::updateStep () {
	ZLIntVec2D vec = getVector( mX, mY );
	mDx = vec.mX;
	mDy = vec.mY;
	if ( mDx != 0 )	mX += ( mDx > 0 ? 1 : -1 );
	if ( mDy != 0 ) mY += ( mDy > 0 ? 1 : -1 );
}

#define ALLOW_DIAGONAL true

ZLIntVec2D TMInfluenceMapWalker::getVector ( u32 x0, u32 y0 ) {
	u32 x1 = x0 ;
	u32 y1 = y0 ;
	float score = calcScore( x0, y0 );
	float score1 = score;
	if ( ( score1 = calcScore( x0 + 1, y0 + 0 ) ) > score ) {
		score = score1;
		x1 = x0 + 1;  y1 = y0 + 0;
	}
	if ( ( score1 = calcScore( x0 + 0, y0 + 1 ) ) > score ) {
		score = score1;
		x1 = x0 + 0;  y1 = y0 + 1;
	}
	if ( ( score1 = calcScore( x0 - 1, y0 + 0 ) ) > score ) {
		score = score1;
		x1 = x0 - 1;  y1 = y0 + 0;
	}
	if ( ( score1 = calcScore( x0 + 0, y0 - 1 ) ) > score ) {
		score = score1;
		x1 = x0 + 0;  y1 = y0 - 1;
	}

	if( ALLOW_DIAGONAL ){
		if ( ( score1 = calcScore( x0 + 1, y0 + 1 ) ) > score ) {
			score = score1;
			x1 = x0 + 1;  y1 = y0 + 1;
		}
		if ( ( score1 = calcScore( x0 - 1, y0 + 1 ) ) > score ) {
			score = score1;
			x1 = x0 - 1;  y1 = y0 + 1;
		}
		if ( ( score1 = calcScore( x0 - 1, y0 - 1 ) ) > score ) {
			score = score1;
			x1 = x0 - 1;  y1 = y0 - 1 ;
		}
		if ( ( score1 = calcScore( x0 + 1, y0 - 1 ) ) > score ) {
			score = score1;
			x1 = x0 + 1;  y1 = y0 - 1;
		}
	}
	return ZLIntVec2D( x1 - x0 , y1 - y0 );
}


//----------------------------------------------------------------//
void TMInfluenceMapWalker::RegisterLuaClass ( MOAILuaState& state ) {
	UNUSED( state );
}

void TMInfluenceMapWalker::RegisterLuaFuncs ( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		{ "reserve",     _reserve },
		{ "setMap",      _setMap },
		{ "updateStep",  _updateStep },
		{ "setLoc",      _setLoc },
		{ "getLoc",      _getLoc },
		{ "addLoc",      _addLoc },
		{ "calcScore",   _calcScore },
		{ "getVector",   _getVector },
		{ NULL, NULL }
	};

	luaL_register( state, 0, regTable );
}


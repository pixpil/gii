
#include <MDDMapObject.h>

//----------------------------------------------------------------//
//GLUE
int MDDMapObject::_setTeamFlags ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UN" )
	u32 teamFlags = state.GetValue<u32>( 2, 0 );
	self->mTeamFlags = teamFlags;
	return 0;
}

int MDDMapObject::_setPassFlags ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UN" )
	u32 passFlags = state.GetValue<u32>( 2, 0 );
	self->mPassFlags = passFlags;
	return 0;
}


int MDDMapObject::_isVisible ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	state.Push( self->IsVisible() );
	return 1;
}

int MDDMapObject::_setVisible ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	bool visible = state.GetValue<bool>( 2, true );
	self->SetVisible( visible );
	return 0;
}

int MDDMapObject::_setVisionPassFlags ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UN" )
	u32 passFlags = state.GetValue<u32>( 2, 0 );
	self->mVisionPassFlags = passFlags;
	return 0;
}

int MDDMapObject::_setCollisionFlags ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UNN" )
	u32 flags = state.GetValue<u32>( 2, 0xffff );
	u32 mask  = state.GetValue<u32>( 3, 0xffff );
	self->mCollisionFlags = flags;
	self->mCollisionMask  = mask;
	return 0;
}

int MDDMapObject::_setCollisionListener ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	self->mOnObjectCollision.SetRef( *self, state, 2 );
	self->mOnTileCollision.SetRef( *self, state, 3 );
	return 0;
}

int MDDMapObject::_setSpeed ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UN" )
	float speed = state.GetValue<float>( 2, 0 );
	self->mSpeed = speed;
	return 0;
}

int MDDMapObject::_setTarget ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UNN" )
	float x = state.GetValue<float>( 2, 0.0f );
	float y = state.GetValue<float>( 3, 0.0f );
	self->setTarget( ZLVec2D( x, y ) );
	return 0;
}


int MDDMapObject::_setRadius ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UNNN" )
	float radius            = state.GetValue<float>( 2, 0.0f );
	float radiusAvoidWall   = state.GetValue<float>( 3, 0.0f );
	float radiusAvoidObject = state.GetValue<float>( 4, 0.0f );
	self->setRadius( radius, radiusAvoidWall, radiusAvoidObject );
	return 0;
}


int MDDMapObject::_setPushing ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	self->setPushing( state.GetValue<bool>( 2, true ) );
	return 0;
}

int MDDMapObject::_setPushable ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	self->setPushable( state.GetValue<bool>( 2, true ) );
	return 0;
}


int MDDMapObject::_canSeeObject ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UU" )
	MDDMapObject *obj = state.GetLuaObject< MDDMapObject >( 2, true );
	if ( !obj ) return 0 ;
	state.Push( self->canSeeObject( *obj ) );
	return 1;
}

int MDDMapObject::_canSeeTile ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UNN" )
	u32 x = state.GetValue<u32>( 2, 1 ) - 1;
	u32 y = state.GetValue<u32>( 3, 1 ) - 1;
	state.Push( self->canSeeTile( x, y ) );
	return 1;
}


int MDDMapObject::_pushWayPoint ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UNN" )
	float x = state.GetValue<float>( 2, 1 ) - 1;
	float y = state.GetValue<float>( 3, 1 ) - 1;
	self->pushWayPoint( ZLVec2D( x, y ) );
	return 0;
}


int MDDMapObject::_clearWayPoints ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	self->clearWayPoints( );
	return 0;
}

int MDDMapObject::_hasWayPoint ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	state.Push( self->mTarget != 0 || !self->mWayPoints.empty() );
	return 1;
}


int MDDMapObject::_updateStep ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	float dt    = state.GetValue<float>( 2, 0 );
	u32   phase = state.GetValue<u32>( 3, 0 );
	bool  arrived = false;
	if( phase == 0 ){
		arrived = self->computeTarget( dt );
		self->mLoc.mX += self->mVectorTarget.mX * dt * self->mSpeed ;
		self->mLoc.mY += self->mVectorTarget.mY * dt * self->mSpeed ;
		self->computeObjectCollision();
	} else if ( phase == 1 ) {
		// self->computeWallCollision();
	}
	self->ScheduleUpdate ();
	state.Push( arrived );
	return 1;
}


int MDDMapObject::_getCellCoord ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	MOAICellCoord coord = self->getCellCoord();
	state.Push( coord.mX + 1 );
	state.Push( coord.mY + 1 );
	return 2;
}

int MDDMapObject::_setCellCoord ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	u32 x = state.GetValue<u32>( 2, 1 ) - 1;
	u32 y = state.GetValue<u32>( 3, 1 ) - 1;
	self->setCellCoord( x, y );
	return 0;
}

int MDDMapObject::_getVectorFacing ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	state.Push( self->mVectorFacing.mX );
	state.Push( self->mVectorFacing.mY );
	return 2;
}


int MDDMapObject::_getVectorTarget ( lua_State * L ){
	MOAI_LUA_SETUP( MDDMapObject, "U" )
	state.Push( self->mVectorTarget.mX );
	state.Push( self->mVectorTarget.mY );
	return 2;
}


int MDDMapObject::_findSeeableObjects ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UN" )	
	float radius = state.GetValue<float>( 2, 10 );

	STLList< MDDMapObject* > list;
	typedef STLList< MDDMapObject* >::iterator iterator;
	// u32 collided = 0;
	ZLVec3D loc = self->GetLoc();
	float tileSize = self->mMap->mTileSize;
	u32 count = self->mMap->objectInCircle( list, loc.mX, loc.mY, radius * tileSize );

	if( !count ) return 0;
	
	lua_newtable( state );
	u32 seeableCount = 0;
	iterator it = list.begin ();
	for ( ; it != list.end (); ++it ) {
		MDDMapObject* o = *it;
		if( o == self ) continue;
		if( !self->canSeeObject( *o ) ) continue;
		seeableCount++;
		state.Push( seeableCount );
		o->PushLuaUserdata( state );
		lua_settable( state, -3 );
	}

	if( seeableCount ) return 1;
	return 0;
}


int MDDMapObject::_moveTowardObject ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UUN" )
	MDDMapObject *obj = state.GetLuaObject< MDDMapObject >( 2, true );
	float chaseRadius = state.GetValue<float>( 3, 10 );
	state.Push( self->moveTowardObject( *obj, chaseRadius ) );
	return 1;
}


int MDDMapObject::_moveAwayFromObject ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UUN" )
	MDDMapObject *obj = state.GetLuaObject< MDDMapObject >( 2, true );
	float safeRadius = state.GetValue<float>( 3, 10 );
	//TODO
	self->moveAwayFromObject( *obj, safeRadius );
	return 0;
}


int MDDMapObject::_moveToward ( lua_State *L ) {
	MOAI_LUA_SETUP( MDDMapObject, "UNN" )
	float x = state.GetValue<float>( 2, 0.0f );
	float y = state.GetValue<float>( 3, 0.0f );
	self->moveToward( ZLVec2D( x, y ) );
	return 0;
}

//----------------------------------------------------------------//
//META
void MDDMapObject::RegisterLuaClass ( MOAILuaState& state ){
	UNUSED( state );
}

void MDDMapObject::RegisterLuaFuncs ( MOAILuaState& state ){
	MOAIProp::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		{ "setTeamFlags",         _setTeamFlags },
		{ "setPassFlags",         _setPassFlags },
		{ "setVisionPassFlags",   _setVisionPassFlags },
		{ "setCollisionFlags",    _setCollisionFlags },
		{ "setCollisionListener", _setCollisionListener },

		{ "setTarget",            _setTarget },
		{ "setSpeed",             _setSpeed },
		{ "setRadius",            _setRadius },
		{ "setPushing",           _setPushing },
		{ "setPushable",          _setPushable },

		{ "canSeeObject",         _canSeeObject },
		{ "canSeeTile",           _canSeeTile },
		{ "findSeeableObjects",   _findSeeableObjects },

		{ "getCellCoord",         _getCellCoord},
		{ "setCellCoord",         _setCellCoord},
		{ "getVectorFacing",      _getVectorFacing},
		{ "getVectorTarget",      _getVectorTarget},

		{ "clearWayPoints",       _clearWayPoints },
		{ "pushWayPoint",         _pushWayPoint },
		{ "hasWayPoint",          _hasWayPoint },

		{ "updateStep",           _updateStep },
		
		{ "moveTowardObject",     _moveTowardObject },
		{ "moveAwayFromObject",   _moveAwayFromObject },
		{ "moveToward",           _moveToward },

		{ "isVisible",            _isVisible },
		{ "setVisible",           _setVisible },

		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );

}

MDDMapObject::MDDMapObject () :
	mVisionPassFlags   (0),
	mFlags             ( FLAGS_VISIBLE ),
	mPassFlags         (0),
	mTeamFlags         (0),
	mMotionFlags       ( MOTION_FLAGS_PUSHING | MOTION_FLAGS_PUSHABLE ),
	mCollisionMask     (0),
	mCollisionFlags    (0),
	mSpeed             (0),
	mGroup             (0),
	mRadius            (0),
	mRadiusAvoidObject (0),
	mRadiusAvoidWall   (0),
	mRadiusArrival     (0),
	mTarget            (0),
	mVectorFacing      ( 0.0f, 0.0f ),
	mVectorTarget      ( 0.0f, 0.0f ),
	mVectorAvoidance   ( 0.0f, 0.0f ),
	mVectorInfluence   ( 0.0f, 0.0f ),
	mWeightAvoid       (0),
	mMap               (0)
{
	RTTI_BEGIN
		RTTI_EXTEND(MOAIProp)
	RTTI_END
}

MDDMapObject::~MDDMapObject () {
}



//----------------------------------------------------------------//
//IMPLEMENTATION


bool MDDMapObject::computeTarget ( float delta ) {

	if( !mTarget ){
		if( mWayPoints.empty() ) return true;
		ZLVec2D wp;
		u32 i = 0;
		for ( u32 i = 0; i < 1; i++ ) {
		// while(1) {
			//fetch future waypoint in sight( to smooth path )
			ZLVec2D wp1 = mWayPoints.front();
			if( canDirectVisitPoint( wp1.mX, wp1.mY ) ) { 
				wp = wp1;
			} else {
				if ( i == 0 ) {//unreachable waypoint
					mWayPoints.pop_front();
					return false;
				}
				break;
			}
			i++;
			mWayPoints.pop_front();
			if( mWayPoints.empty() ) break ;
		}
		ZLVec2D *p = new ZLVec2D( wp.mX, wp.mY );
		mTarget = p; 
	}

	mVectorTarget.Init( *mTarget );
	mVectorTarget.Sub( ZLVec2D( mLoc.mX, mLoc.mY ) );
	if( isRunningAway() ) {
		mVectorTarget.Reverse();
	}
	
	float length = mVectorTarget.Length();
	if( length <= max( delta * mSpeed, mRadiusArrival ) ){
		//reached waypoint
		mVectorTarget = ZLVec2D( 0.0f, 0.0f );		
		clearTarget();
	} else {
		mVectorTarget.Norm();		
	}
	return false;
}

int MDDMapObject::computeObjectCollision () {
	//TODO: should we use a central collision manager? or use sweep&prunze ?
	//using moaipartition for broadphase
	
	// if( !this->isPushable() ) 
	// 	return 0;

	MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();

	int collisionCount = 0;
	mWeightAvoid = 0.0f;
	STLList< MDDMapObject* > list;
	typedef STLList< MDDMapObject* >::iterator iterator;

	float x = mLoc.mX;
	float y = mLoc.mY;
	float radius = mRadius;
	
	u32 count = mMap->objectInCircle( list, x, y, radius );
	// printf( "%d\n", count );
	ZLVec2D avoid ( 0.0f, 0.0f );
	if( count ){
		iterator it = list.begin ();
		for ( ; it != list.end (); ++it ) {
			MDDMapObject* o = *it;
			if( o == this ) continue;

			ZLVec2D diff ( x - o->mLoc.mX,	y - o->mLoc.mY );
			float interception = ( o->mRadius + radius ) - diff.Length();

			if ( interception > 0.0f ) { //collided
				//collision callback
				if( (o->mCollisionFlags & mCollisionMask)==0 ) continue;
				if( this->mOnObjectCollision ) {
					this->mOnObjectCollision.PushRef( state );
					this->PushLuaUserdata( state );
					o->PushLuaUserdata( state );
					state.DebugCall ( 2, 1 );
					//TODO: response according to return value
					if( !state.GetValue<bool>( -1, true ) ) continue;
				}

				//respond
				continue;
				if( !o->isPushing()  ) continue;
				float k;
				if ( diff.mX == 0.0f && diff.mY == 0.0f ) { 
					// move to random direction if interception == 0
					diff.mX = (float)(rand() % 100);
					diff.mY = (float)(rand() % 100);
				}				
				diff.NormSafe();
				if ( !o->isPushable() ){
					diff.Scale( interception );
					mLoc.mX += diff.mX;
					mLoc.mY += diff.mY;
				} else if ( isFriendTeam(*o) ) {
					diff.Scale( interception * 0.5f );
					mLoc.mX    += diff.mX;
					mLoc.mY    += diff.mY;
					o->mLoc.mX -= diff.mX;
					o->mLoc.mY -= diff.mY;
				} else if( o->mRadius > radius ) { //big push small
					diff.Scale( interception );
					mLoc.mX += diff.mX;
					mLoc.mY += diff.mY;
				} else {
					diff.Scale( interception );
					o->mLoc.mX -= diff.mX;
					o->mLoc.mY -= diff.mY;
				}
				collisionCount++;
			}
		}
	}
	return collisionCount;
}

int MDDMapObject::computeWallCollision () {
	TMPathGrid* grid = mMap->mPathGrid;
	//determine check cells
	float x = mLoc.mX;
	float y = mLoc.mY;
	// float radius = mRadius;
	float radius = mRadius;
	float radius2 = radius * radius;
	float tileSize = mMap->mTileSize;
	MOAICellCoord coordMin = mMap->getCellCoord( x - radius, y - radius );
	MOAICellCoord coordMax = mMap->getCellCoord( x + radius, y + radius );
	//max vector on each side
	float vx = mVectorTarget.mX;
	float vy = mVectorTarget.mY;

	bool collided = false;
	for ( int ty = coordMin.mY; ty <= coordMax.mY; ++ty )
	for ( int tx = coordMin.mX; tx <= coordMax.mX; ++tx )
	{
		if( ! grid->isTileBlocked( tx, ty, mPassFlags, mTeamFlags ) )	continue;
		float cx = ((float)tx + 0.5 ) * tileSize;
		float cy = ((float)ty + 0.5 ) * tileSize;
		float dirX = cx > x ? -1 : 1; //direction of edges to compare to
		float dirY = cy > y ? -1 : 1;
		float ex = cx + dirX * tileSize/2; //edge to compare to
		float ey = cy + dirY * tileSize/2;
		float dx, dy, dx2, dy2;
		
		dx = x - ex; dx2 = dx * dx; //distance to closest edges
		dy = y - ey; dy2 = dy * dy;

		
		if ( 
			!( ( dx2 + dy2 ) < radius2 || ( dx2 < radius2 || dy2 < radius2 ) ) 
			) continue ; 
	
		// soft collision
		bool xConnected = grid->isTileBlocked( tx + dirX, ty, mPassFlags, mTeamFlags );
		bool yConnected = grid->isTileBlocked( tx, ty + dirY, mPassFlags, mTeamFlags );
		dx *= dirX; dy *= dirY;
		
		bool avoidX =!xConnected && dx > 0;
		bool avoidY =!yConnected && dy > 0;

		float ix = radius - dx;
		float iy = radius - dy;

		if( avoidX && ix > 0 ) {
			collided = true;
			x += ix * dirX;
		} else if( avoidY && iy > 0 ) {
			collided = true;
			y += iy * dirY;
		}
	} // end of for
	mLoc.mX = x;
	mLoc.mY = y;
	if ( collided ) {
		MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();
		if( this->mOnTileCollision ) {
			this->mOnTileCollision.PushRef( state );
			this->PushLuaUserdata( state );
			state.DebugCall ( 1, 1 );
			//TODO: send tile location as parameter?
			//TODO: response according to return value
		}
	}
	return collided;
}

int MDDMapObject::checkTileState () {
	MOAICellCoord coord = getCellCoord();
	u32 flag = mMap->mFlagGrid->GetTile( coord.mX, coord.mY );
	if( flag & MDDMap::TILEMASK_VISITED ){
		this->SetVisible( true );
	}
	return 0;
}

bool MDDMapObject::updateStep ( float delta ) {
	//update object speed
	bool arrived = computeTarget( delta );
	mLoc.mX += mVectorTarget.mX * delta * mSpeed ;
	mLoc.mY += mVectorTarget.mY * delta * mSpeed ;
	//collision process
	this->computeObjectCollision();
	this->computeWallCollision();	
	return arrived;
}

bool MDDMapObject::update ( float delta, u32 phase ) {
	//update object speed
	if( phase == 0 ) {
		bool arrived = computeTarget( delta );
		mLoc.mX += mVectorTarget.mX * delta * mSpeed ;
		mLoc.mY += mVectorTarget.mY * delta * mSpeed ;
		//collision process
		this->computeObjectCollision();
		return arrived;
	}
	if( phase == 1 ) {
		this->computeWallCollision();
		this->checkTileState();
	}
	return true;
}


MOAICellCoord MDDMapObject::getCellCoord () {
	ZLVec3D loc = this->GetLoc();
	return mMap->getCellCoord( loc.mX, loc.mY );
}

void MDDMapObject::setCellCoord ( u32 x, u32 y ) {
	ZLVec2D loc = mMap->getTileLoc( x, y );
	mLoc.mX = loc.mX;
	mLoc.mY = loc.mY;
}

bool MDDMapObject::canSeeObject( MDDMapObject& obj ){
	return this->canSeePoint( obj.mLoc.mX, obj.mLoc.mY );
}

bool MDDMapObject::canSeeTile( u32 x, u32 y ) {
	MOAICellCoord coord = getCellCoord();
	return mMap->mPathGrid->isSeeable( x, y, coord.mX, coord.mY, mVisionPassFlags, mTeamFlags );
}

bool MDDMapObject::canSeePoint( float x, float y ) {
	return mMap->mPathGrid->isSeeablePoint( mLoc.mX, mLoc.mY, x, y, mVisionPassFlags, mTeamFlags );
}

bool MDDMapObject::canDirectVisitTile( u32 x, u32 y ) {
	MOAICellCoord coord = getCellCoord();
	return mMap->mPathGrid->isSeeable( coord.mX, coord.mY, x, y, mPassFlags, mTeamFlags );
}

bool MDDMapObject::canDirectVisitPoint( float x, float y ) {
	return mMap->mPathGrid->isSeeablePoint( mLoc.mX, mLoc.mY, x, y, mPassFlags, mTeamFlags );
}

void MDDMapObject::setRadius( float radius, float radiusAvoidWall, float radiusAvoidObject ) {
	mRadius            = radius;
	mRadiusAvoidWall   = radiusAvoidWall;	
	mRadiusAvoidObject = radiusAvoidObject;
	//update bounds with object avoidance radius
	float boundDim = mRadius;
	mBoundsOverride.Init( 
		-boundDim, -boundDim,
		 boundDim,  boundDim,
		-boundDim,  boundDim
		);
	mRadiusArrival = mRadius;
	mFlags |= FLAGS_OVERRIDE_BOUNDS;
	ScheduleUpdate();
}

//----------------------------------------------------------------//
void MDDMapObject::pushWayPoint ( ZLVec2D wayPoint ) {
	mWayPoints.push_back( wayPoint );
	clearTarget();
}

void MDDMapObject::clearWayPoints () {
	mWayPoints.clear();
	clearTarget();
}

//----------------------------------------------------------------//
void MDDMapObject::setTarget ( const ZLVec2D& target ) {	
	mTarget = new ZLVec2D( target.mX, target.mY );
}

void MDDMapObject::clearTarget() {
	if ( !mTarget ) return ;
	delete mTarget;
	mTarget = NULL;
	mVectorTarget = ZLVec2D( 0, 0 );
	setRunningAway( false );
}

bool MDDMapObject::moveTowardObject( MDDMapObject& obj, float chaseRadius ) {
	ZLVec3D loc1 = obj.GetLoc();
	ZLVec3D diff = loc1 - mLoc;
	float distance = diff.Length();
	if ( distance <= chaseRadius ) {
		clearTarget();
		return true;
	}
	setTarget( ZLVec2D( loc1.mX, loc1.mY ) );
	return false;
}

bool MDDMapObject::moveAwayFromObject( MDDMapObject& obj, float safeRadius ) {
	//TODO
	ZLVec3D loc1 = obj.GetLoc();
	ZLVec3D diff = loc1 - mLoc;
	float distance = diff.Length();
	if ( distance >= safeRadius ) {
		clearTarget();
		return true;
	}
	setTarget( ZLVec2D( loc1.mX, loc1.mY ) );
	setRunningAway( true );
	return false;
}

void MDDMapObject::moveToward( ZLVec2D vec ) {
	clearTarget();
	mVectorTarget = vec;
}


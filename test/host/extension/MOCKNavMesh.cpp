#include "MOCKNavMesh.h"
#include "ZLVecMap.h"
#include <float.h>


//----------------------------------------------------------------//
MOCKNavMeshFaceQuadtree::MOCKNavMeshFaceQuadtree() :
mNumFacesToGrow( 4 ),
mNodes( 0 ),
mIsLeaf( true )
{
	mBound.Init( 0.0f, 0.0f, 0.0f, 0.0f );
}


MOCKNavMeshFaceQuadtree::MOCKNavMeshFaceQuadtree( float _left, float _right, float _top, float _down, u32 _numObjectsToGrow ) :
mNumFacesToGrow( _numObjectsToGrow ),
mNodes( 0 ),
mIsLeaf( true )
{
	mBound.Init( _left, _top, _right, _down );
}

//----------------------------------------------------------------//
MOCKNavMeshFaceQuadtree::~MOCKNavMeshFaceQuadtree()
{
	if ( !mIsLeaf )
		delete [] mNodes;
}

//----------------------------------------------------------------//
void MOCKNavMeshFaceQuadtree::AddFace( MOCKNavMeshFace *face )
{
	if ( mIsLeaf ) {
		mFaces.push_back( face );
		bool reachedMaxFaces = ( mFaces.size() == mNumFacesToGrow );
		if ( reachedMaxFaces ) {
			this->CreateLeaves();
			this->MoveFacesToLeaves();
			mIsLeaf = false;
		}
		return;
	}

	for ( int n = 0; n < NodeCount; ++n ) {
		if ( mNodes[n].Contains( face ) ) {
			mNodes[n].AddFace( face );
			return;
		}
	}

	mFaces.push_back( face );
}

//----------------------------------------------------------------//
void MOCKNavMeshFaceQuadtree::Clear()
{
	mFaces.clear();

	if ( !mIsLeaf ) {
		for ( int n = 0; n < NodeCount; ++n ) {
			mNodes[n].Clear();
		}
	}
}

//----------------------------------------------------------------//
STLArray< MOCKNavMeshFace* > MOCKNavMeshFaceQuadtree::GetFacesAt( float x, float y, u32 querySeq ) {
	STLArray< MOCKNavMeshFace* > result = this->GetFacesAt( x, y );
	STLArray< MOCKNavMeshFace* > cleaned;

	u32 faceCount = result.size();
	for( int n = 0; n < faceCount; ++n ) {
		MOCKNavMeshFace* face = result[ n ];
		if( face->mQuerySeq != querySeq ) {
			face->mQuerySeq = querySeq;
			cleaned.push_back( face );
		}
	}
	return cleaned;
}

STLArray< MOCKNavMeshFace* > MOCKNavMeshFaceQuadtree::GetFacesAt( float x, float y ) {
	if ( mIsLeaf ) {
		return mFaces;
	}
	STLArray< MOCKNavMeshFace* > returnedFaces;
	STLArray< MOCKNavMeshFace* > childFaces;

	if ( !mFaces.empty() ) {
		returnedFaces.insert( returnedFaces.end(), mFaces.begin(), mFaces.end() );
	}

	for ( int n = 0; n < NodeCount; ++n ) {
		if ( mNodes[n].Contains( x, y ) ) {
			childFaces = mNodes[n].GetFacesAt( x, y );
			returnedFaces.insert( returnedFaces.end(), childFaces.begin(), childFaces.end() );
			break;
		}
	}
	
	return returnedFaces;
}

//----------------------------------------------------------------//
bool MOCKNavMeshFaceQuadtree::Contains( MOCKNavMeshFace *face )
{
	return face->InsideRect( this->mBound );
}

//----------------------------------------------------------------//
bool MOCKNavMeshFaceQuadtree::Contains( float x, float y )
{
	// printf("contains %.1f,%.1f,%.1f,%.1f\n", mBound.mXMin, mBound.mYMin, mBound.mXMax, mBound.mYMax);
	return this->mBound.Contains( x, y );
}

//----------------------------------------------------------------//
void MOCKNavMeshFaceQuadtree::CreateLeaves()
{
	mNodes = new MOCKNavMeshFaceQuadtree[4];
	mNodes[NW] = MOCKNavMeshFaceQuadtree( mBound.mXMin, (mBound.mXMin+mBound.mXMax)/2, mBound.mYMin, (mBound.mYMin+mBound.mYMax)/2, mNumFacesToGrow );
	mNodes[NE] = MOCKNavMeshFaceQuadtree( (mBound.mXMin+mBound.mXMax)/2, mBound.mXMax, mBound.mYMin, (mBound.mYMin+mBound.mYMax)/2, mNumFacesToGrow );
	mNodes[SW] = MOCKNavMeshFaceQuadtree( mBound.mXMin, (mBound.mXMin+mBound.mXMax)/2, (mBound.mYMin+mBound.mYMax)/2, mBound.mYMax, mNumFacesToGrow );
	mNodes[SE] = MOCKNavMeshFaceQuadtree( (mBound.mXMin+mBound.mXMax)/2, mBound.mXMax, (mBound.mYMin+mBound.mYMax)/2, mBound.mYMax, mNumFacesToGrow );
}

//----------------------------------------------------------------//
void MOCKNavMeshFaceQuadtree::MoveFacesToLeaves()
{
	for ( int n = 0; n < NodeCount; ++n ) {
		for ( u32 m = 0; m < mFaces.size(); ++m ) {
			if ( mNodes[n].Contains( mFaces[m] ) ) {
				mNodes[n].AddFace( mFaces[m] );
				mFaces.erase( mFaces.begin() + m );
				--m;
			}
		}
	}
}


//----------------------------------------------------------------//
//----------------------------------------------------------------//
inline u32 MakeEdgeId( u32 id1, u32 id2 ) {
	if( id1 > id2 ) {
		return ( id1 << 16 ) | ( id2 & 0xffff );
	} else {
		return ( id2 << 16 ) | ( id1 & 0xffff );
	}
}


//----------------------------------------------------------------//
float MOCKNavMeshFace::Side(const ZLVec3D &v0, const ZLVec3D &v1, const ZLVec3D &v)
{
	ZLVec3D e = v1 - v0;
	ZLVec3D f = v - v0;
	ZLVec3D n( -e.mY, e.mX, 0.0f );
	return n.Dot( f );
}

//----------------------------------------------------------------//
//----------------------------------------------------------------//
void MOCKNavMeshFace::Init ( u32 size ) {
	this->mQuerySeq = 0;
	this->mSize = size;
	this->mNeighbors.Init( size );
	this->mVerts.Init( size );
	this->mVertIds.Init( size );
	for( int i = 0; i < size; ++i ) {
		this->mNeighbors[ i ] = NULL;
		this->mVertIds[ i ] = -1;
	}
}

//----------------------------------------------------------------//
void MOCKNavMeshFace::Init ( MOCKPolyPath* path ) {
	u32 size = path->GetVertCount();
	this->Init( size );
	for( int i = 0; i < size; ++i ) {
		this->mVerts[ i ].Init( path->GetVert( i ) );
	}
	this->UpdateInfo();
}

//----------------------------------------------------------------//
bool MOCKNavMeshFace::InsideRect( ZLRect rect ) {
	if( !rect.Contains( this->mBound ) ) return false;
	u32 size = this->mVerts.Size();
	for( int i = 0; i < size; ++i ) {
		const ZLVec3D &v = this->mVerts[ i ];
		if( !rect.Contains( v.mX, v.mY ) ) return false;
	}
	return true;
}


//----------------------------------------------------------------//
bool MOCKNavMeshFace::IsInside ( const ZLVec3D& p ) {
	u32 size = this->mSize;
	for( u32 i = 0; i < size; ++i ) {
		if( MOCKNavMeshFace::Side( this->mVerts[ i ], this->mVerts[ (i+1) % size ], p ) < 0 ) return false;
	}
	return true;
}


//----------------------------------------------------------------//
MOCKNavMeshFace* MOCKNavMeshFace::GetNeighbor ( u32 idx ) {
	return this->mNeighbors[ idx ];
}

//----------------------------------------------------------------//
int MOCKNavMeshFace::FindNeighorIndex ( MOCKNavMeshFace* face ) {
	u32 size = this->mSize;
	for( u32 i = 0; i < size; ++i ) {
		if( this->mNeighbors[ i ] == face ) return i;
	}
	return -1;
}

//----------------------------------------------------------------//
ZLVec3D MOCKNavMeshFace::GetVert ( u32 idx, bool wrapped ) {
	return this->mVerts[ wrapped ? idx % this->mSize : idx ];
}

//----------------------------------------------------------------//
void MOCKNavMeshFace::SetNeighbor ( MOCKNavMeshEdge& edge, MOCKNavMeshFace* face ) {
	u32 size = this->mSize;
	// printf( "adding neighbor %d %d (%d,%d)\n", mId, face->mId, edge.mVA, edge.mVB );
	for( int i = 0; i < size; ++i ) {
		u32 v0 = this->mVertIds[ i ];
		u32 v1 = this->mVertIds[ ( i + 1 ) % size ];
		if( ( v0 == edge.mVA || v0 == edge.mVB ) && ( v1 == edge.mVA || v1 == edge.mVB ) ) {
			// printf( "!! %d[%d]->%d  @%d\n", mId, i, face->mId, v0 );
			this->mNeighbors[ i ] = face;
			return;
		}
	}
	assert( false );
}

//----------------------------------------------------------------//
void MOCKNavMeshFace::UpdateInfo () {
	//update center
	ZLRect bound;
	bound.Init( FLT_MAX, FLT_MAX, -FLT_MAX, -FLT_MAX );
	
	ZLVec3D center;
	if( this->mSize> 0 ) {
		for( int i = 0; i < this->mSize; ++i ) {
			const ZLVec3D &v = this->mVerts[ i ];
			center.Add( v );
			ZLVec2D xy;
			xy.Init( v.mX, v.mY );
			bound.Grow( xy );
		}
		center.Scale( 1.0/this->mSize );
	}
	this->mCenter.Init( center );
	this->mBound = bound;
	// printf("face %.1f,%.1f,%.1f,%.1f\n", mBound.mXMin, mBound.mYMin, mBound.mXMax, mBound.mYMax);
}

//----------------------------------------------------------------//
//----------------------------------------------------------------//
MOCKNavMeshEdge::MOCKNavMeshEdge () :
	mVA( 0 ), mVB( 0 ),
	mFA( NULL ),
	mFB( NULL ) {
}

void MOCKNavMeshEdge::AddFace( MOCKNavMeshFace* face ) {
	if( this->mFA == face ) return;
	if( this->mFB == face ) return;
	if( this->mFA == NULL ) { this->mFA = face; return; }
	if( this->mFB == NULL ) { this->mFB = face; return; }
	//shouldn't be here
	assert( false );
}


//----------------------------------------------------------------//
//----------------------------------------------------------------//
int MOCKNavMesh::_buildFromPolyPaths ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNavMesh, "UT" )

	u32 top = state.GetTop();
	u32 size = lua_objlen( L, 2 );
	if ( size == 0 ) return 0;

	u32 count = 0;
	self->Reserve( size );
	lua_pushnil ( L ); //initial key
	while ( lua_next ( L, 2 ) != 0 ) {
		MOCKPolyPath* polyPath = state.GetLuaObject < MOCKPolyPath >( -1, 0 );
		if ( polyPath ) {
			self->SetFace( count, polyPath );
		}
		lua_pop ( L, 1 ); //key stay
		count++;
	}
	self->BuildGraph();

	return 0;
}

int MOCKNavMesh::_clear ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNavMesh, "U" )
	self->Clear();
	return 0;
}

int MOCKNavMesh::_findNavigationPath ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNavMesh, "UNNNNT" )
	// Start & TargetPoint
	float x0 = state.GetValue < float >( 2, 0.0f );
	float y0 = state.GetValue < float >( 3, 0.0f );
	float x1 = state.GetValue < float >( 4, 0.0f );
	float y1 = state.GetValue < float >( 5, 0.0f );
	//node path
	ZLLeanArray< u32 > nodePath;
	u32 size = lua_objlen( L, 6 );
	u32 i = 0;
	nodePath.Init( size );
	lua_pushnil ( L ); //initial key
	while ( lua_next ( L, 6 ) != 0 ) {
		u32 nodeId = state.GetValue < u32 >( -1, 1 ) - 1;
		nodePath[ i ] = nodeId;
		lua_pop ( L, 1 ); //key stay
		i++;
	}

	ZLLeanArray< ZLVec3D > naviPath;
	bool found = self->FindNavigationPath( ZLVec3D( x0, y0, 0.0f ), ZLVec3D( x1, y1, 0.0f ), nodePath, naviPath );
	if( !found ) return 0;

	int count = naviPath.Size();
	lua_createtable( L, count * 2, 0 );
	for( int i = 0; i < count; ++i ) {
		lua_pushnumber( L, naviPath[ i ].mX );
		lua_rawseti( L, -2, i * 2 + 1 );
		lua_pushnumber( L, naviPath[ i ].mY );
		lua_rawseti( L, -2, i * 2 + 2 );
	}
	return 1;
}

int MOCKNavMesh::_getNodeAtPoint ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNavMesh, "UNN" )
	ZLVec3D loc = state.GetVec3D< float >( 2 );
	MOCKNavMeshFace* face = self->GetFaceAtPoint( loc );
	if( face ) {
		state.Push( face->GetID() + 1 );
	} else {
		state.Push();
	}
	return 1;
}

//----------------------------------------------------------------//
void MOCKNavMesh::BuildGraph () {
	//set vert id

	u32 id1, id2;
	this->mEdgeMap.clear();
	u32 count = this->mFaces.Size();
	for( u32 i = 0; i < count; ++i ) {
		MOCKNavMeshFace* face = this->GetFace( i );
		if( !face ) continue;
		u32 vcount = face->mSize;
		id1 = this->AffirmVertId( face->mVerts[ vcount - 1 ] );
		for( u32 j = 0; j < vcount; ++j ){
			id2 = this->AffirmVertId( face->mVerts[ j ] );
			face->mVertIds[ j ] = id2;
			this->AffirmEdge( id1, id2 ).AddFace( face );
			id1 = id2;
		}
	}
	//set neighbor
	MOCKNavMeshEdgeMap::iterator it = this->mEdgeMap.begin();
	while( it != this->mEdgeMap.end() ) {
		MOCKNavMeshEdge& edge = it->second;
		if( edge.mFA && edge.mFB ) {
			// printf("----\n neighbor %d->%d\n", edge.mFA->mId, edge.mFB->mId );
			edge.mFA->SetNeighbor( edge, edge.mFB );
			edge.mFB->SetNeighbor( edge, edge.mFA );
		}
		++it;
	}
	//insert into quadTree
	ZLRect bound;
	bound.Init( FLT_MAX, FLT_MAX, -FLT_MAX, -FLT_MAX );

	for( u32 i = 0; i < count; ++i ) {
		MOCKNavMeshFace* face = this->GetFace( i );
		if( !face ) continue;
		bound.Grow( face->mBound );
	}
	this->mTree.mBound = bound;
	// printf("%.1f,%.1f,%.1f,%.1f\n", bound.mXMin, bound.mYMin, bound.mXMax, bound.mYMax);
	for( u32 i = 0; i < count; ++i ) {
		MOCKNavMeshFace* face = this->GetFace( i );
		if( !face ) continue;
		this->mTree.AddFace( face );
	}
}

//----------------------------------------------------------------//
void MOCKNavMesh::PushNeighbors( MOAIPathFinder& pathFinder, int nodeID ) {
	MOCKNavMeshFace* currentNode = this->GetFace( nodeID );

	if( !currentNode ) return;

	MOCKNavMeshFace* targetNode = this->GetFace ( pathFinder.GetTargetNodeID ());

	u32 vertCount = currentNode->mSize;
	for( u32 i = 0; i < vertCount; ++i ) {
		MOCKNavMeshFace* neighbor = currentNode->mNeighbors[ i ];
		int neighborId = -1;
		if ( neighbor ) neighborId = neighbor->mId;

		if ( neighbor && !pathFinder.IsVisited( neighbor->mId ) ) {
			float g = neighbor->mCenter.DistSqrd ( currentNode->mCenter ) * pathFinder.GetGWeight ();
			float h = neighbor->mCenter.DistSqrd ( targetNode->mCenter ) * pathFinder.GetHWeight ();
			pathFinder.PushState( neighbor->mId, g, h );
			// printf( "requesting neighbor:%d->%d  for:%d\n", nodeID, neighborId, targetNode->mId );
		}
	}

}

//----------------------------------------------------------------//
bool MOCKNavMesh::FindNavigationPath ( 
	const ZLVec3D& start, const ZLVec3D& target, 	const ZLLeanArray< u32 >& nodePath, ZLLeanArray< ZLVec3D >& output
) {
	ZLLeanStack< ZLVec3D > path;
	u32 size = nodePath.Size();
	if( size < 1 ) return false;
	//Collect Portal Points
	ZLLeanArray< ZLVec3D > portalListLeft;
	ZLLeanArray< ZLVec3D > portalListRight;
	portalListLeft.Init( size );
	portalListRight.Init( size );
	for ( int i = 0; i < size - 1; ++i )
	{
		MOCKNavMeshFace* node  = this->GetFace( nodePath[ i ]  );
		MOCKNavMeshFace* node1 = this->GetFace( nodePath[ i+1 ] );
		if( !( node && node1 ) ) return false;  //no node found
		int idx = node->FindNeighorIndex( node1 );
		if( idx < 0 ) return false; //not neighbor
		portalListRight [ i ] = node->GetVert( idx );
		portalListLeft  [ i ] = node->GetVert( idx + 1 );
	}
	//set target as final portal
	portalListRight[ size - 1 ].Init( target );
	portalListLeft [ size - 1 ].Init( target );

	//main course
	ZLVec3D apex = start;
	path.Push( start );

	ZLVec3D left  = start;
	ZLVec3D right = start;
	int idx = 0;
	int idxApex  = 0;
	int idxLeft  = 0;
	int idxRight = 0;
	while ( idx < size ) {
		//test left
		ZLVec3D newLeft  = portalListLeft[ idx ];
		float sideL = MOCKNavMeshFace::Side( apex, left, newLeft );
		if( sideL <= 0.0f ) {
			if( sideL < 0.0f &&  MOCKNavMeshFace::Side( apex, right, newLeft ) < 0.0f ) { //tighten
				apex = right;
				idx = idxRight;
				path.Push( apex );
				continue; //reset
			} 
			left = newLeft;
			idxLeft = idx;
		}
		//test right
		ZLVec3D newRight = portalListRight[ idx ];
		float sideR = MOCKNavMeshFace::Side( apex, right, newRight );
		if( sideR >= 0.0f ) {
			if( sideR > 0.0f && MOCKNavMeshFace::Side( apex, left, newRight ) > 0.0f ) { //tighten
				apex = left;
				idx = idxLeft;
				path.Push( apex );
				continue; //reset
			}
			right = newRight;
			idxRight = idx;
		}
		idx++;
	}

	//TODO!
	path.Push( target );
	output.Init( path.GetTop() );
	output.CopyFrom( path );
	return true;
}


//----------------------------------------------------------------//
void MOCKNavMesh::Clear () {
	this->mVertMap.clear();
	this->mVertCount = 0;
}

//----------------------------------------------------------------//
void MOCKNavMesh::SetFace ( u32 idx, MOCKPolyPath* path ) {
	u32 count = path->GetVertCount();
	MOCKNavMeshFace* face = this->GetFace( idx );
	if ( face ) {
		face->Init( path );
	}
}

//----------------------------------------------------------------//
MOCKNavMeshFace* MOCKNavMesh::GetFace ( u32 idx ) {
	if ( idx < this->mFaces.Size() ) {
		return &this->mFaces[ idx ];
	}
	return NULL;
}

//----------------------------------------------------------------//
MOCKNavMeshFace* MOCKNavMesh::GetFaceAtPoint ( const ZLVec3D& loc ) {
	//TODO: use MOCKNavMeshFaceQuadtree	
	this->mQuerySeq++;
	STLArray< MOCKNavMeshFace* > candidates = this->mTree.GetFacesAt( loc.mX, loc.mY, this->mQuerySeq );
	u32 count = candidates.size();
	// printf("finding face:%.1f,%.1f in %d, %d \n", loc.mX, loc.mY, count, this->mFaces.Size() );
	for ( int i = 0; i < count; ++i )	{
		MOCKNavMeshFace* face = candidates[i];
		if ( face->IsInside( loc ) ) return face;
	}
	return NULL;
}

//----------------------------------------------------------------//
u32 MOCKNavMesh::AffirmVertId ( ZLVec3D vert ) {
	ZLVec2D v2;
	v2.Init( vert.mX, vert.mY );
	ZLVec2DMap< u32 >::iterator it = this->mVertMap.find( v2 );
	// ZLVec3DMap< u32 >::iterator it = this->mVertMap.find( v2 );
	if( it == this->mVertMap.end() ) {
		u32 newId = this->mVertCount++;
		this->mVertMap[ v2 ] = newId;
		return newId;
	}
	return it->second;
}

//----------------------------------------------------------------//
MOCKNavMeshEdge& MOCKNavMesh::AffirmEdge ( u32 vertId1, u32 vertId2 ) {
	u32 id = MakeEdgeId( vertId1, vertId2 );
	MOCKNavMeshEdgeMap::iterator iter = this->mEdgeMap.find( id );
	if( iter == this->mEdgeMap.end() ) {
		MOCKNavMeshEdge edge;
		edge.mVA = vertId1;
		edge.mVB = vertId2;
		std::pair< MOCKNavMeshEdgeMap::iterator, bool > ret;
		ret = this->mEdgeMap.insert( std::pair< u32, MOCKNavMeshEdge >( id, edge ) );
		return ret.first->second;
	} else {
		return iter->second;
	}
}

//----------------------------------------------------------------//
void MOCKNavMesh::Reserve ( u32 count ) {
	this->Clear();
	this->mFaces.Init( count );
	for( u32 i = 0; i < count; i++ ) {
		this->mFaces[i].mId = i;
	}
}


//----------------------------------------------------------------//
MOCKNavMesh::MOCKNavMesh () :
	mVertCount( 0 ),
	mQuerySeq( 0 )
{
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIPathGraph )
	RTTI_END
}

MOCKNavMesh::~MOCKNavMesh () {
	this->Clear();
}

//----------------------------------------------------------------//
void MOCKNavMesh::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIPathGraph::RegisterLuaClass( state );
}

void MOCKNavMesh::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIPathGraph::RegisterLuaFuncs( state );

	luaL_Reg regTable [] = {
		{ "buildFromPolyPaths",	_buildFromPolyPaths },
		{ "clear",		          _clear              },
		{ "findNavigationPath",	_findNavigationPath },
		{ "getNodeAtPoint",	    _getNodeAtPoint     },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}


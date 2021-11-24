#ifndef MOCKNAVMESH_H
#define MOCKNAVMESH_H

#include "moai-sim/headers.h"
#include "MOCKPolyPath.h"
#include "ZLVecMap.h"

class MOCKNavMesh;
class MOCKNavMeshFaceQuadtree;
class MOCKNavMeshFace;
class MOCKNavMeshEdge;


//----------------------------------------------------------------//
class MOCKNavMeshFaceQuadtree {
	friend class MOCKNavMeshFace;
	friend class MOCKNavMesh;
	enum Node {
			NW = 0,
			NE,
			SW,
			SE,
			NodeCount
	};

	private:
		ZLRect mBound;

		u32 mNumFacesToGrow;
		STLArray < MOCKNavMeshFace * > mFaces;
		MOCKNavMeshFaceQuadtree * mNodes;
		bool mIsLeaf;
		bool Contains( MOCKNavMeshFace * face );
		bool Contains( float x, float y );
		void CreateLeaves();
		void MoveFacesToLeaves();

	public:
		MOCKNavMeshFaceQuadtree();
		MOCKNavMeshFaceQuadtree(float left, float right, float top, float down, unsigned int numFacesToGrow = 3);
		~MOCKNavMeshFaceQuadtree();

		void AddFace(MOCKNavMeshFace * face);
		void Clear();
		STLArray < MOCKNavMeshFace* > GetFacesAt( float x, float y );
		STLArray < MOCKNavMeshFace* > GetFacesAt( float x, float y, u32 querySeq );

};

//----------------------------------------------------------------//
class MOCKNavMeshFace {
private:
	friend class MOCKNavMesh;
	friend class MOCKNavMeshFaceQuadtree;

	u32 mQuerySeq;

	u32 mId;
	u32 mSize;
	ZLLeanArray< ZLVec3D > mVerts;
	ZLLeanArray< int > mVertIds;
	ZLLeanArray< MOCKNavMeshFace* > mNeighbors;
	ZLVec3D mCenter;

	ZLRect mBound;
	
	void Init          ( u32 Size );
	void Init          ( MOCKPolyPath* path );
	void SetNeighbor  ( MOCKNavMeshEdge& edge, MOCKNavMeshFace* face );

	static inline float Side ( const ZLVec3D &v0, const ZLVec3D &v1, const ZLVec3D &v );

public:

	GET ( ZLVec3D, Center, mCenter );
	GET ( u32, ID, mId );

	void UpdateInfo ();
	bool IsInside ( const ZLVec3D& p );
	ZLVec3D GetVert( u32 idx, bool wrapped = true );

	MOCKNavMeshFace* GetNeighbor   ( u32 idx );
	int FindNeighorIndex ( MOCKNavMeshFace* face );
	bool InsideRect ( ZLRect rect );

};


//----------------------------------------------------------------//
class MOCKNavMeshEdge
{
private:
	friend class MOCKNavMesh;
	friend class MOCKNavMeshFace;
	u32 mVA;
	u32 mVB;
	MOCKNavMeshFace* mFA;
	MOCKNavMeshFace* mFB;

	void AddFace( MOCKNavMeshFace* face );

public:
	MOCKNavMeshEdge();
};

typedef STLMap< u32, MOCKNavMeshEdge > MOCKNavMeshEdgeMap;

//----------------------------------------------------------------//
class MOCKNavMesh:
	public MOAIPathGraph
{
private:
	// static int _reserve      ( lua_State* L );
	static int _buildFromPolyPaths ( lua_State* L );
	static int _clear              ( lua_State* L );
	static int _findNavigationPath ( lua_State* L );
	static int _getNodeAtPoint     ( lua_State* L );
	
	//
	u32 mQuerySeq;
	//
	ZLLeanArray< MOCKNavMeshFace > mFaces;
	ZLVec2DMap< u32 > mVertMap;
	MOCKNavMeshEdgeMap mEdgeMap;
	u32 mVertCount;

	u32 AffirmVertId( ZLVec3D vert );
	MOCKNavMeshEdge& AffirmEdge( u32 vertId1, u32 vertId2 );

	MOCKNavMeshFaceQuadtree mTree;

protected:
	virtual void	PushNeighbors			( MOAIPathFinder& pathFinder, int nodeID );

public:

	void             BuildGraph   ();
	void             Clear        ();
	MOCKNavMeshFace* GetFace      ( u32 idx );
	void             Reserve      ( u32 count );
	void             SetFace      ( u32 idx, MOCKPolyPath* path );

	MOCKNavMeshFace* GetFaceAtPoint ( const ZLVec3D& loc );

	bool             FindNavigationPath ( const ZLVec3D& start, const ZLVec3D& target, const ZLLeanArray< u32 >& nodePath, ZLLeanArray< ZLVec3D >& output );

	DECL_LUA_FACTORY ( MOCKNavMesh )
	
	MOCKNavMesh();
	~MOCKNavMesh();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};


#endif

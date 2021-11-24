#ifndef	TMPATHGRID_H
#define	TMPATHGRID_H


#include <moai-sim/headers.h>
#include <moai-sim/MOAIPathGraph.h>

#define MAX_SECTION_COUNT 4096


//----------------------------------------------------------------//
class TMPathSection
{
public:
	u32 mId;
	u32 mCode;
	u32 mPassMask;
	u32 mTeamMask;
	u32 mSeq;
		
	STLSet <TMPathSection *> mNeighbors;
	void dropAll();
	void addNeighbor(TMPathSection* section);
	bool hasNeighbor(TMPathSection* section);
	bool isAlone();
	bool isJustChecked();
	bool checkConnected(TMPathSection* target, u32 passFlags, u32 teamFlags, bool noEnter);
	
	bool checkFlags(u32 passFlags, u32 teamFlags){
		return ((mPassMask & passFlags)!=0) && ((mTeamMask & teamFlags)!=0) ;
	}
};

//----------------------------------------------------------------//
struct TMPathGridTileType{
	u32 mCode;
	u32 mPassMask;
	u32 mTeamMask;
};

//----------------------------------------------------------------//
class TMPathSectionList{
private:
	ZLLeanArray <TMPathSection*> mArray;
	u32 mSize;
	int mPointer;
	
public:
	TMPathSectionList(u32 size){
		mArray.Init(size);
		mArray.Fill(0);
		mPointer=0;
		mSize=size;
	}

	~TMPathSectionList(){}
	
	bool insert(TMPathSection* sec){
		//find next empty slot
		int entry=mPointer; 
		while(1){
			int oldPointer=mPointer;
			mPointer=(mPointer + 1) % mSize;

			if(mArray[oldPointer]==0){
				mArray[oldPointer]=sec;
				sec->mId=oldPointer;
				return true;
			}

			if(mPointer==entry) return false;
		}
	}

	void clear(){
		for(int i=0;i<mArray.Size();i++){
			TMPathSection* s=mArray[i];
			if(s!=0) delete s;
		}
	}

	void remove(int id){
		mArray[id]=0;
	}

	TMPathSection* get(int id){
		return mArray[id];
	}

};


//----------------------------------------------------------------//
class TMPathGrid:
	public virtual MOAIPathGraph
{
private:
	class PathGraphParam {
	public:

		float mHCost;
		float mVCost;
		float mDCost;
		float mZCost;

		float mGWeight;
		float mHWeight;
		
		u32 mHeuristic;
	};

	static int _setTile(lua_State *L);
	static int _getTile(lua_State *L);
	static int _getSectionId(lua_State *L);
	static int _getCodeGrid(lua_State *L);
	static int _getSectionGrid(lua_State *L);
	static int _isReachable(lua_State *L);
	static int _isSeeable(lua_State *L);
	static int _isTileBlocked(lua_State *L);
	static int _getSeeableCells(lua_State *L);
	static int _setDefaultPassFlags(lua_State *L);
	static int _setDefaultTeamFlags(lua_State *L);

	static int _init(lua_State *L);
	static int _registerTileType(lua_State* L);

	float mTileWidth;
	float mTileHeight;

	u32 mWidth, mHeight, mPartitionWidth, mPartitionHeight;
	u32 mMaxSection;
	u32 mDefaultPassFlags;
	u32 mDefaultTeamFlags;

	u32 mNeighborSeq;

	TMPathSection* mEmptySection;
	TMPathSectionList mSections;
	ZLLeanArray<u32> mSectionSeqs;

	MOAILuaSharedPtr<MOAIGrid> mSectionGrid;
	MOAILuaSharedPtr<MOAIGrid> mCodeGrid;

	
	STLMap	<u32,TMPathGridTileType*> mTileTypes;

	TMPathSection* allocateSection(u32 code);
	TMPathSection* reallocateSection(TMPathSection* section);
	void removeSection(TMPathSection* section);	
	
	//----------------------------------------------------------------//
	float			ComputeHeuristic			( PathGraphParam& params, const MOAICellCoord& c0, const MOAICellCoord& c1 );
	u32				ComputeClearance		( MOAIPathFinder& pathFinder, int xTile, int yTile);
	void			PushNeighbor				( MOAIPathFinder& pathFinder, PathGraphParam& params, u32 tile0, int xTile, int yTile, float moveCost );
	void			PushNeighbors				( MOAIPathFinder& pathFinder, int nodeID );

public:

	DECL_LUA_FACTORY (TMPathGrid)

	TMPathGrid();
	~TMPathGrid();

	void	init( u32 width, u32 height, float tileWidth, float tileHeight, u32 partitionWidth, u32 partitionHeight );

	TMPathSection* 	setTile(u32 x, u32 y, u32 code);	//set tiletype code, returns section
	u32 	getSectionId(u32 x, u32 y);
	
	TMPathSection* getSection(u32 x, u32 y);

	u32 	getTile(u32 x, u32 y);
	

	bool isReachable     ( int x0, int y0, int x1, int y1, u32 passFlags, u32 teamFlags, bool noEnter );
	bool isSeeable       ( u32 x0, u32 y0, u32 x1, u32 y1, u32 passFlags, u32 teamFlags );
	bool isSeeablePoint  ( float x0, float y0, float x1, float y1, u32 passFlags, u32 TeamFlags );
	
	bool isTileBlocked(u32 x, u32 y, u32 passFlags, u32 teamFlags);

	void	registerTileType(u32 code, u32 passMask, u32 teamMask);

	void			RegisterLuaClass		( MOAILuaState& state );
	void			RegisterLuaFuncs		( MOAILuaState& state );

};


#endif
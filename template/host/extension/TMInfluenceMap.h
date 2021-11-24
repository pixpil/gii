#ifndef	TMINFLUENCEMAP_H
#define	TMINFLUENCEMAP_H

#include <moai-sim/headers.h>

#define INFLUENCEMAP_USE_DOUBLE_BUFFER 1

//----------------------------------------------------------------//
class TMInfluenceMap:
	public virtual MOAILuaObject {

private:

	static int _init         ( lua_State *L );
	static int _clearMap     ( lua_State *L );
	static int _getCell      ( lua_State *L );
	static int _setCell      ( lua_State *L );
	static int _addCell      ( lua_State *L );

	static int _update       ( lua_State *L );

	u32 mWidth;
	u32 mHeight;
	u32 mDecayType;

	float mDecayRate;
	float mDiffusionRate;

	u32 mCurrentMapId;

	ZLLeanArray< float > mMap0;
	ZLLeanArray< float > mMap1; //double buffer


public:

	enum {
		DECAY_LINEAR,
		DECAY_EXPONENTIAL
	};

	DECL_LUA_FACTORY( TMInfluenceMap )

	void   init            ( u32 width, u32 height, u32 decayType, float decayRate, float diffusionRate );
	void   clearMap        ();
	float  getCell         ( u32 x, u32 y );
	void   setCell         ( u32 x, u32 y, float value );
	void   addCell         ( u32 x, u32 y, float value );
	void   updateDiffusion ( u32 iteration );
	
	inline ZLLeanArray< float > * getCurrentMap(){
		#if INFLUENCEMAP_USE_DOUBLE_BUFFER
			ZLLeanArray< float > * map = mCurrentMapId == 0 ? &mMap0 : &mMap1;
		#else
			ZLLeanArray< float > * map = &mMap0;
		#endif
		return map;
	}

	TMInfluenceMap  ();
	~TMInfluenceMap ();

	void RegisterLuaClass ( MOAILuaState& state );
	void RegisterLuaFuncs ( MOAILuaState& state );

	/* data */
};



//----------------------------------------------------------------//
class TMInfluenceMapWalkerConfig {
public:
	MOAILuaSharedPtr< TMInfluenceMap > mMap;
	float mWeight;
	float mMultiplier;	
	float mOffset;
};


//----------------------------------------------------------------//

class TMInfluenceMapWalker:
	public virtual MOAILuaObject {

private:

	static int _reserve      ( lua_State *L );
	static int _setMap       ( lua_State *L );
	static int _updateStep   ( lua_State *L );
	static int _setLoc       ( lua_State *L );
	static int _getLoc       ( lua_State *L );
	static int _addLoc       ( lua_State *L );
	static int _calcScore    ( lua_State *L );
	static int _getVector    ( lua_State *L );


	ZLLeanArray < TMInfluenceMapWalkerConfig > mConfigs;

	u32 mX, mY ;
	int mDx, mDy ;


public:

	DECL_LUA_FACTORY ( TMInfluenceMapWalker )

	GET ( u32, X, mX )
	GET ( u32, Y, mY )
	
	TMInfluenceMapWalker();
	~TMInfluenceMapWalker();

	void        reserve    ( u32 count );
	void        setMap     ( u32 id, TMInfluenceMap* map, float weight, float offset, float multiplier );
	void        updateStep ( );
	float       calcScore  ( u32 x, u32 y );
	ZLIntVec2D  getVector  ( u32 x0, u32 y0 );
	
	void  RegisterLuaClass ( MOAILuaState& state );
	void  RegisterLuaFuncs ( MOAILuaState& state );
};

#endif

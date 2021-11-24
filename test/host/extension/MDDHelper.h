#ifndef	MDDHELPER_H
#define	MDDHELPER_H
#include <moai-sim/headers.h>

class MDDHelper:
	public ZLContextClass < MDDHelper, MOAILuaObject > 
{
private:
	
	//----------------------------------------------------------------//
	static int _getSeeableCells(lua_State *L);
	static int _canSeeCell(lua_State *L);
	static int _blockAction(lua_State *L);
	static int _fillGrid(lua_State *L);

	static int _tileToBits(lua_State *L);
	static int _bitsToTile(lua_State *L);
	static int _setTileBit(lua_State *L);
	static int _getTileBit(lua_State *L);

	static int _distanceBetweenTransform(lua_State *L);


	// static int _isBlocked(lua_State *L);
	// static int _getActionStat(lua_State *L);
	// static int _setActionPass(lua_State *L);
public:
	
	DECL_LUA_SINGLETON ( MDDHelper )

	static bool canSeeCell(MOAIGrid* grid, int x0,int y0,int x1,int y1);

	//----------------------------------------------------------------//
	MDDHelper();
	~MDDHelper();
	
	void			RegisterLuaClass	( MOAILuaState& state );
};


#endif
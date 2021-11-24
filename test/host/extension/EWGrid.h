#ifndef EWGRID_H
#define EWGRID_H

#include "moai-sim/headers.h"

class EWGrid :
	public MOAIGrid
{
private:

public:
	DECL_LUA_FACTORY ( EWGrid )
	
	void Draw ( MOAIDeck *deck, MOAIDeckRemapper *remapper, const MOAICellCoord &c0, const MOAICellCoord &c1 ) ;

	EWGrid();
	~EWGrid();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif
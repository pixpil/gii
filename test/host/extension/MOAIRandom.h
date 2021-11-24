#ifndef MOAIRANDOM_H
#define MOAIRANDOM_H

//================================================================//
// MOAIRandom
//================================================================//
// TODO: doxygen
class MOAIRandom :
	public MOAILuaObject{
private:
		struct SFMT_T*	mSFMT;
		//----------------------------------------------------------------//
		static int		_rand			( lua_State* L );
		static int		_seed			( lua_State* L );

public:
	
	DECL_LUA_FACTORY ( MOAIRandom )

	//----------------------------------------------------------------//
					MOAIRandom			();
					~MOAIRandom			();
	void    RegisterLuaClass ( MOAILuaState& state );
	void    RegisterLuaFuncs ( MOAILuaState& state );
};

#endif

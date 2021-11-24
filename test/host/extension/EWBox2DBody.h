#ifndef EWBOX2DBODY_H
#define EWBOX2DBODY_H

#include "moai-box2d/headers.h"
class EWBox2DWorld;

class EWBox2DBody :
	public MOAIBox2DBody
{
private:
	friend class EWBox2DWorld;

	static int _setupContactFilter ( lua_State* L );

	// static int _setWorld  					 ( lua_State* L );
	// static int _getLocZ   					 ( lua_State* L );
	// static int _setLocZ   					 ( lua_State* L );
	static int _getFloor						 ( lua_State* L );
	static int _setFloor						 ( lua_State* L );
	static int _getHeight 					 ( lua_State* L );
	static int _setHeight 					 ( lua_State* L );
	static int _forceRefilter				 ( lua_State* L );

	// float mLocZ;
	// float mHeight;

	int   mFloor;
	float mHeight;

	bool			ApplyAttrOp				( u32 attrID, MOAIAttrOp& attrOp, u32 op );


	void 			RefilterAttachedFixtures();

public:
	// GET_SET ( float, LocZ,  mLocZ  )
	GET ( int, Floor, mFloor )
	GET ( float, Height, mHeight )

	void SetFloor(int floor);
	void SetHeight(float height);

	inline bool ShouldCollide ( EWBox2DBody* bodyB ) {

		// float u2m =  this->GetUnitsToMeters();
		// if( bodyB->mLocZ + bodyB->mHeight * u2m + EPSILON < this->mLocZ ) 
		// 		return false;
		// if( bodyB->mLocZ > this->mLocZ + this->mHeight * u2m + EPSILON ) 
		// 		return false;

		if (bodyB->GetFloor() + bodyB->GetHeight() < this->GetFloor())
		{
			return false;
		}

		if (bodyB->GetFloor() > this->GetFloor() + this->GetHeight())
		{
			return false;
		}

		return true;
	};

	DECL_LUA_FACTORY ( EWBox2DBody )

	EWBox2DBody();
	~EWBox2DBody();

	void				RegisterLuaClass		( MOAILuaState& state );
	void				RegisterLuaFuncs		( MOAILuaState& state );

};

#endif
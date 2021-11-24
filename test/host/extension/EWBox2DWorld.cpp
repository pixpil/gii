#include "EWBox2DWorld.h"
#include "EWBox2DBody.h"

//----------------------------------------------------------------//
class EWBox2DContactFilter :
	public b2ContactFilter
{
public:
	bool ShouldCollide( b2Fixture* fixtureA, b2Fixture* fixtureB ) {
		bool result = false;
		MOAIBox2DBody* bodyA = ( MOAIBox2DBody* )fixtureA->GetBody()->GetUserData ();
		MOAIBox2DBody* bodyB = ( MOAIBox2DBody* )fixtureB->GetBody()->GetUserData ();
		EWBox2DBody* ewBodyA = bodyA->AsType < EWBox2DBody >();
		EWBox2DBody* ewBodyB = bodyB->AsType < EWBox2DBody >();
		if( ewBodyA && ewBodyB ) {
			result = ewBodyA->ShouldCollide( ewBodyB );
			result &= b2ContactFilter::ShouldCollide(fixtureA, fixtureB);
		} else {
			result = b2ContactFilter::ShouldCollide(fixtureA, fixtureB);
		}

		return result;
	}
};


static EWBox2DContactFilter s_contactFilter;


int EWBox2DWorld::_addEWBody ( lua_State* L ) {
	MOAI_LUA_SETUP ( EWBox2DWorld, "UN" )
	
	if ( self->IsLocked ()) {
		MOAILog ( state, MOAILogMessages::MOAIBox2DWorld_IsLocked );
		return 0;
	}
	
	float u2m = self->GetUnitsToMeters();
	u32 type	= state.GetValue < u32 >( 2, 0 );
	float x		= state.GetValue < float >( 3, 0.0f ) * u2m;
	float y		= state.GetValue < float >( 4, 0.0f ) * u2m;
	
	b2BodyDef groundBodyDef;
	groundBodyDef.type = ( b2BodyType )type;
	groundBodyDef.position.Set ( x, y );
	EWBox2DBody* body = new EWBox2DBody ();
	body->SetBody ( self->GetWorld()->CreateBody ( &groundBodyDef ));
	body->SetWorld ( self );
	self->LuaRetain ( body );
	
	body->PushLuaUserdata ( state );

	return 1;
}

EWBox2DWorld::EWBox2DWorld () :
MOAIBox2DWorld()
{
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIBox2DWorld )
	RTTI_END

	this->GetWorld()->SetContactFilter(&s_contactFilter);
}

EWBox2DWorld::~EWBox2DWorld () {

	this->GetWorld()->SetContactFilter(NULL);
}

void EWBox2DWorld::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIBox2DWorld::RegisterLuaClass ( state );
}

void EWBox2DWorld::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIBox2DWorld::RegisterLuaFuncs ( state );

	luaL_Reg regTable [] = {
		{ "addEWBody",         _addEWBody },
		{ NULL, NULL }
	};
	luaL_register ( state, 0, regTable );
}

#include "EWBox2DBody.h"


//----------------------------------------------------------------//
// int EWBox2DBody::_setupContactFilter( lua_State* L ) {
// 	MOAILuaState state ( L );
// 	MOAIBox2DWorld* world = state.GetLuaObject < MOAIBox2DWorld >( 1, 0 );
// 	//TODO:need destroy support
// 	EWBox2DContactFilter* filter = new EWBox2DContactFilter(); 
// 	if ( !world ) return 0;
// 	world->GetWorld()->SetContactFilter( filter );
// 	return 0;
// }

// int EWBox2DBody::_setLocZ ( lua_State *L ) {
// 	MOAI_LUA_SETUP( EWBox2DBody, "UN" )
// 	int f = state.GetValue < float >( 2, 0.0f );
// 	self->SetLocZ( f );
// 	return 0;
// }

// int EWBox2DBody::_getLocZ ( lua_State *L ) {
// 	MOAI_LUA_SETUP( EWBox2DBody, "U" )
// 	state.Push( self->GetLocZ() );
// 	return 1;
// }

int EWBox2DBody::_setFloor ( lua_State *L ) {
	MOAI_LUA_SETUP( EWBox2DBody, "UN" )
	int f = state.GetValue < int >( 2, 0 );
	self->SetFloor( f );
	return 0;
}

int EWBox2DBody::_getFloor ( lua_State *L ) {
	MOAI_LUA_SETUP( EWBox2DBody, "U" )
	state.Push( self->GetFloor() );
	return 1;
}

int EWBox2DBody::_setHeight ( lua_State *L ) {
	MOAI_LUA_SETUP( EWBox2DBody, "UN" )
	int h = state.GetValue < float >( 2, 0.0f );
	self->SetHeight( h );
	return 0;
}

int EWBox2DBody::_getHeight ( lua_State *L ) {
	MOAI_LUA_SETUP( EWBox2DBody, "U" )
	state.Push( self->GetHeight() );
	return 1;
}

// int EWBox2DBody::_setWorld ( lua_State *L ) {
// 	MOAI_LUA_SETUP( EWBox2DBody, "UU" )
	
// 	MOAIBox2DWorld* world = state.GetLuaObject < MOAIBox2DWorld >( 2, 0 );
// 	if ( !world ) return 0;
// 	if ( world->IsLocked ()) {
// 		MOAILog ( state, MOAILogMessages::MOAIBox2DWorld_IsLocked );
// 		return 0;
// 	}
	
// 	u32 type	= state.GetValue < u32 >( 3, 0 );
// 	float x		= state.GetValue < float >( 4, 0.0f ) * world->GetUnitsToMeters();
// 	float y		= state.GetValue < float >( 5, 0.0f ) * world->GetUnitsToMeters();
	
// 	b2BodyDef groundBodyDef;
// 	groundBodyDef.type = ( b2BodyType )type;
// 	groundBodyDef.position.Set ( x, y );
	
// 	// MOAIBox2DBody* body = new MOAIBox2DBody ();
// 	self->SetBody ( world->GetWorld()->CreateBody ( &groundBodyDef ));
// 	self->SetWorld ( world );
// 	world->LuaRetain ( self );
// 	return 0;
// }

int EWBox2DBody::_forceRefilter(lua_State *L)
{
	MOAI_LUA_SETUP( EWBox2DBody, "U" )
	self->RefilterAttachedFixtures();

	return 0;
}

//----------------------------------------------------------------//
EWBox2DBody::EWBox2DBody () :
	MOAIBox2DBody(),
	mFloor( 0 ),
	mHeight( 0.5f )
{
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIBox2DBody )
	RTTI_END
}

EWBox2DBody::~EWBox2DBody () {
}

void EWBox2DBody::SetFloor(int floor)
{
	mFloor = floor;
	RefilterAttachedFixtures();

}


void EWBox2DBody::SetHeight(float height)
{
	mHeight = height;

	RefilterAttachedFixtures();
}

void EWBox2DBody::RefilterAttachedFixtures()
{
	for(b2Fixture* f = GetBody()->GetFixtureList(); f; f = f->GetNext())
	{
		f->Refilter();
	}
}

//----------------------------------------------------------------//
bool EWBox2DBody::ApplyAttrOp ( u32 attrID, MOAIAttrOp& attrOp, u32 op ) {
	// TODO: these values may need to be cached for performance reasons
	if ( MOAITransform::MOAITransformAttr::Check ( attrID )) {
		b2Body* body = this->GetBody();
		const b2Transform & xform = body->GetTransform();
		
		switch ( UNPACK_ATTR ( attrID )) {
			case MOAITransform::ATTR_X_LOC: {
				float x = attrOp.Apply ( xform.p.x, op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT ) * this->GetUnitsToMeters ();
				body->SetTransform ( b2Vec2( x, xform.p.y), xform.q.GetAngle() );
				return true;
			}
				
			case MOAITransform::ATTR_Y_LOC: {
				float y = attrOp.Apply ( xform.p.y, op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT ) * this->GetUnitsToMeters ();
				body->SetTransform ( b2Vec2( xform.p.x, y ), xform.q.GetAngle() );
				return true;
			}

			case MOAITransform::ATTR_Z_LOC: {
				// float z = attrOp.Apply ( this->mLocZ, op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT ) * this->GetUnitsToMeters ();
				// this->SetLocZ( z );
				return true;
			}
				
			case MOAITransform::ATTR_Z_ROT: {
				float angle = attrOp.Apply ( (float)( xform.q.GetAngle() * R2D ), op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT );
				body->SetTransform ( xform.p,  ( float )(angle * D2R) );
				return true;
			}
		}
	}
	return MOAITransformBase::ApplyAttrOp (attrID, attrOp, op );
}


//----------------------------------------------------------------//
void EWBox2DBody::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIBox2DBody::RegisterLuaClass ( state );
	// luaL_Reg regTable [] = {
	// 	{ "setupContactFilter",         _setupContactFilter },
	// 	{ NULL, NULL }
	// };
	// luaL_register ( state, 0, regTable );
}

void EWBox2DBody::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIBox2DBody::RegisterLuaFuncs ( state );
	luaL_Reg regTable [] = {
		// { "setWorld",               _setWorld  },
		// { "getLocZ",                _getLocZ  },
		// { "setLocZ",                _setLocZ  },
		{ "getFloor",               _getFloor  },
		{ "setFloor",               _setFloor  },
		{ "getHeight",              _getHeight },
		{ "setHeight",              _setHeight },
		{ "forceRefilter", 					_forceRefilter},
		{ NULL, NULL }
	};
	luaL_register ( state, 0, regTable );
}

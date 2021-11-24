#include <GIIHelper.h>

int GIIHelper::_stepSim( lua_State *L ){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "N" )) return 0;
	double step = state.GetValue< double >( 1, 0.0f );
	GIIHelper::Get().stepSim( step );
	return 0;
}

int GIIHelper::_forceGC( lua_State *L){
	MOAILuaState state (L);
	// MOAILuaRuntime::Get ().ForceGarbageCollection ();
	return 0;
}

int GIIHelper::_setBufferSize( lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "NN" )) return 0;
	u32 width=state.GetValue<u32>(1, 0);
	u32 height=state.GetValue<u32>(2, 0);
	MOAIGfxDevice::Get ().SetBufferSize ( width, height );
	return 0;
}

// int GIIHelper::_clearFrameBuffer( lua_State *L ){
// 	MOAILuaState state (L);
// 	if ( !state.CheckParams ( 1, "U" )) return 0;
// 	MOAIFrameBuffer* frameBuffer = state.GetLuaObject < MOAIFrameBuffer >( 1, false );
// 	if (frameBuffer) {
// 		zglBegin();
// 		frameBuffer->ClearSurface();
// 		zglEnd();
// 	}
// 	return 0;
// }

int GIIHelper::_renderFrameBuffer( lua_State *L ){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "U" )) return 0;
	MOAIFrameBuffer* frameBuffer = state.GetLuaObject < MOAIFrameBuffer >( 1, false );
	if (frameBuffer) {
		zglBegin();
		frameBuffer->Render();
		zglEnd();
	}
	return 0;
}

int GIIHelper::_setVertexTransform( lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "U" )) return 0;
	MOAITransform* trans = state.GetLuaObject< MOAITransform >(1, true);
	if ( trans ) {
		MOAIGfxDevice::Get().SetVertexTransform( MOAIGfxDevice::VTX_WORLD_TRANSFORM, trans->GetLocalToWorldMtx() );
	}
	return 0;
}



int GIIHelper::_copyWorldTransform( lua_State *L ){
	ZLAffine3D tmp;
	ZLAffine3D tmp1;
	float rx,ry,rz;
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UU" )) return 0;
	MOAITransform* src = state.GetLuaObject< MOAITransform >(1, true);
	MOAITransform* dst = state.GetLuaObject< MOAITransform >(2, true);
	const ZLAffine3D& srcMtx = src->GetLocalToWorldMtx ();
	const ZLAffine3D* inherit = dst->GetLinkedValue < ZLAffine3D* >( PACK_ATTR ( MOAITransformBase, MOAITransformBase::INHERIT_TRANSFORM ), 0 );	
	tmp.Init( src->GetLocalToWorldMtx() );
	if( inherit ) {
		tmp1.Inverse( *inherit ); 
		tmp.Append( tmp1 );
	}
	ZLVec3D loc   = tmp.GetTranslation();
	ZLVec3D scale = tmp.GetStretch();
	dst->SetLoc( loc );
	dst->SetScl( scale );
	rz = tmp.GetRot();
	dst->SetRot( 0, 0, rz );
	dst->ScheduleUpdate();
	return 0;
}


int GIIHelper::_setWorldLoc( lua_State *L ){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UN" )) return 0;
	MOAITransform* dst = state.GetLuaObject< MOAITransform >(1, true);
	float x = state.GetValue< float >( 2, 0.0f );
	float y = state.GetValue< float >( 3, 0.0f );
	float z = state.GetValue< float >( 4, 0.0f );
	ZLVec3D loc;
	loc.Init( x, y, z );		
	const ZLAffine3D* inherit = dst->GetLinkedValue < ZLAffine3D* >( PACK_ATTR ( MOAITransformBase, MOAITransformBase::INHERIT_TRANSFORM ), 0 );	
	if( inherit ) {
		ZLAffine3D inverse;
		inverse.Inverse( *inherit ); 
		inverse.Transform( loc );
	}
	dst->SetLoc( loc );	
	dst->ScheduleUpdate();
	return 0;
}


void GIIHelper::stepSim( double step ){
	// MOAIInputMgr::Get ().Update ();
	MOAISim::Get().GetActionTree().Update (( float )step );		
	MOAINodeMgr::Get ().Update ();
}


GIIHelper::GIIHelper(){
	RTTI_BEGIN
		RTTI_SINGLE(MOAILuaObject)
	RTTI_END
}

GIIHelper::~GIIHelper(){}

void GIIHelper::RegisterLuaClass(MOAILuaState &state){
	luaL_Reg regTable [] = {
		{ "stepSim",             _stepSim },
		{ "forceGC",             _forceGC },
		{ "setBufferSize",       _setBufferSize },
		{ "renderFrameBuffer",   _renderFrameBuffer },
		{ "setVertexTransform",  _setVertexTransform },
		{ "copyWorldTransform",  _copyWorldTransform },
		{ "setWorldLoc",         _setWorldLoc },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}


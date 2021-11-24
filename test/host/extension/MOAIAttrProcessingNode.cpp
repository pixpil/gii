#include <moai-sim/pch.h>
#include "MOAIAttrProcessingNode.h"

int MOAIAttrProcessingNode::_reserveAttrs ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIAttrProcessingNode, "UN" );

	u32 size = state.GetValue < u32 >( 2, 0 );
	self->mVanillaAttributes.Init ( size );
	self->mVanillaAttributes.Fill ( 0.0f );

	self->mProcessedAttributes.Init ( size );
	self->mProcessedAttributes.Fill ( 0.0f );

	return 0;
}

int MOAIAttrProcessingNode::_setProcessor ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIAttrProcessingNode, "UF" );

	self->mProcessorFunc.SetRef ( *self, state, 2 );
	return 0;
}

bool MOAIAttrProcessingNode::ApplyAttrOp ( u32 attrID, MOAIAttrOp& attrOp, u32 op ) {
	attrID = UNPACK_ATTR(attrID);

	if ( attrID < this->mProcessedAttributes.Size () &&
			 attrID < this->mVanillaAttributes.Size () ) {

		// this->mVanillaAttributes[attrID] = attrOp.Apply ( this->mVanillaAttributes [ attrID ], op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT );
		if (op == MOAIAttrOp::SET)
		{
			float val = attrOp.Apply ( this->mVanillaAttributes [ attrID ], op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT );
			this->mVanillaAttributes [ attrID ] = val;

			if (this->mProcessorFunc)
			{
				MOAIScopedLuaState state = MOAILuaRuntime::Get().State();
				// call user lua function to get massaged value
				if (this->mProcessorFunc.PushRef(state))
				{
					this->PushLuaUserdata(state);
					state.Push(attrID);
					state.Push(val);
					state.DebugCall(3, 1);

					val = state.GetValue<float>(-1, val);
				}
			}
			
			this->mProcessedAttributes [ attrID ] = val;
			
		}
		else
		{
			attrOp.Apply ( this->mProcessedAttributes [ attrID ], op, MOAIAttrOp::ATTR_READ_WRITE, MOAIAttrOp::ATTR_TYPE_FLOAT );
		}
		
		return true;
	}
	return false;
}

MOAIAttrProcessingNode::MOAIAttrProcessingNode()
{
	RTTI_SINGLE (MOAINode)
}

MOAIAttrProcessingNode::~MOAIAttrProcessingNode()
{
}


//----------------------------------------------------------------//
void MOAIAttrProcessingNode::RegisterLuaClass ( MOAILuaState& state ) {

	MOAINode::RegisterLuaClass ( state );
}

//----------------------------------------------------------------//
void MOAIAttrProcessingNode::RegisterLuaFuncs ( MOAILuaState& state ) {
	
	MOAINode::RegisterLuaFuncs ( state );
	
	luaL_Reg regTable [] = {
		{ "reserveAttrs",			_reserveAttrs },
		{ "setProcessor",			_setProcessor },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}
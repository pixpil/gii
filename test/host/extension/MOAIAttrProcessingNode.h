#ifndef MOAIATTRPROCESSINGNODE_H
#define MOAIATTRPROCESSINGNODE_H

#include <moai-sim/MOAINode.h>

class MOAIAttrProcessingNode : public MOAINode
{
	MOAILuaMemberRef mProcessorFunc;

	ZLLeanArray < float > mVanillaAttributes;
	ZLLeanArray < float > mProcessedAttributes;

	static int		_reserveAttrs			( lua_State* L );
	static int		_setProcessor			( lua_State* L );

public:

	DECL_LUA_FACTORY (MOAIAttrProcessingNode)

	MOAIAttrProcessingNode();
	~MOAIAttrProcessingNode();

	bool ApplyAttrOp ( u32 attrID, MOAIAttrOp& attrOp, u32 op );

	void RegisterLuaFuncs ( MOAILuaState& state );
	void RegisterLuaClass ( MOAILuaState& state );


};


#endif // MOAIATTRPROCESSINGNODE_H
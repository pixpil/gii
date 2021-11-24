#include <moai-core/pch.h>
#include <moai-core/MOAILua.h>

#include <extensionClasses.h>

#include <MOAISceneContext.h>

#include <YAKAHelper.h>

#include <MOAISpineSkeleton.h>
#include <MOAISpineSkeletonData.h>
#include <MOAISpineAnimationMixTable.h>
#include <MOAISpineAnimation.h>

#include <MOAITrailProp.h>

#include <MOAIImageLoadTask.h>


#include <MOAIRandom.h>

#include <MOCKNetworkHost.h>
#include <MOCKNetworkBroadcast.h>

#include "MOAISectionDeck.h"
#include "MOAIGradientDeck.h"
#include "MOAIManualTimer.h"

#include "MOAIViewPinTransform.h"

#include "MOAIGfxMaskedQuadListDeck2D.h"

#include "TMPathGrid.h"
#include "TMInfluenceMap.h"


#include "MDDHelper.h"
#include "MDDMap.h"
#include "MDDMapObject.h"
#include "MOCKProp.h"
#include "EWProp.h"


#include "moai-steer/host.h"


void registerExtensionClasses(){	

	REGISTER_LUA_CLASS(MOAISceneContext)
	
	//common system
	REGISTER_LUA_CLASS(MOAIManualTimer)
	REGISTER_LUA_CLASS(MOAIRandom)
	REGISTER_LUA_CLASS(MOAIImageLoadTask)


	//spine
	REGISTER_LUA_CLASS(MOAISpineAtlas)
	REGISTER_LUA_CLASS(MOAISpineSkeletonData)

	REGISTER_LUA_CLASS(MOAISpineSlot)
	REGISTER_LUA_CLASS(MOAISpineSkeleton)
	REGISTER_LUA_CLASS(MOAISpineSkeletonSimple)

	REGISTER_LUA_CLASS(MOAISpineAnimationMixTable)
	REGISTER_LUA_CLASS(MOAISpineAnimation)
	REGISTER_LUA_CLASS(MOAISpineAnimationTrack)
	REGISTER_LUA_CLASS(MOAISpineAnimationSpan)

	//network
	REGISTER_LUA_CLASS(MOCKNetworkHost)
	REGISTER_LUA_CLASS(MOCKNetworkPeer)
	REGISTER_LUA_CLASS(MOCKNetworkBroadcastClient)
	REGISTER_LUA_CLASS(MOCKNetworkBroadcastServer)
	REGISTER_LUA_CLASS(MOCKNetworkRPC)
	
	//graphics helpers
	REGISTER_LUA_CLASS(MOAITrailProp)
	REGISTER_LUA_CLASS(MOAITrailDeck)
	REGISTER_LUA_CLASS(MOAISectionDeck)
	REGISTER_LUA_CLASS(MOAIGradientDeck)
	
	REGISTER_LUA_CLASS(MOAIViewPinTransform)

	REGISTER_LUA_CLASS(MOAIGfxMaskedQuadListDeck2D)
	REGISTER_LUA_CLASS(MOAIGfxMaskedQuadListDeck2DInstance)

	//game specific helper
	REGISTER_LUA_CLASS(YAKAHelper)

	//
	REGISTER_LUA_CLASS(TMPathGrid)
	REGISTER_LUA_CLASS(TMInfluenceMap)
	REGISTER_LUA_CLASS(TMInfluenceMapWalker)
	REGISTER_LUA_CLASS(MDDMap)
	REGISTER_LUA_CLASS(MDDMapObject)
	REGISTER_LUA_CLASS(MDDHelper)
	MDDHelper::Affirm();
	//
	
	REGISTER_LUA_CLASS(MOCKProp)
	REGISTER_LUA_CLASS(EWProp)
	
}


int AKUCreateSceneContext() {
	return 0;
}

void AKUReleaseSceneContext( int id ) {

}

void AKUUpdateSceneContext( int id, double step ) {

}

void AKURenderSceneContext( int id ) {

}

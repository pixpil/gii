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

#include "MOAISectionDeck.h"
#include "MOAIGradientDeck.h"
#include "MOAITileMesh.h"

#include "MOAIManualTimer.h"

#include "MOAIViewPinTransform.h"

#include "MOAIGfxMaskedQuadListDeck2D.h"

#include "MOAIAttrProcessingNode.h"
#include "MOAIGeometry2DDeck.h"

#include "TMPathGrid.h"
#include "TMInfluenceMap.h"


#include "MDDHelper.h"
#include "MDDMap.h"
#include "MDDMapObject.h"
#include "MOCKProp.h"
#include "EWProp.h"
#include "EWDeckCanvasProp.h"
#include "EWPropRenderTransform.h"
#include "EWGrid.h"
#include "EWBox2DWorld.h"
#include "EWBox2DBody.h"
#include "EWBox2DFixture.h"

#include "MOAIMultiShader.h"
#include "MOAIJoystickManagerSDL.h"

#include "moai-steer/host.h"

#include "MOCKPolyPath.h"
#include "MOCKPolyClipper.h"
#include "MOCKPolyPartition.h"
#include "MOCKNavMesh.h"


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

	//graphics helpers
	REGISTER_LUA_CLASS(MOAITrailProp)
	REGISTER_LUA_CLASS(MOAITrailDeck)
	REGISTER_LUA_CLASS(MOAISectionDeck)
	REGISTER_LUA_CLASS(MOAIGradientDeck)
	REGISTER_LUA_CLASS(MOAITileMesh)

	REGISTER_LUA_CLASS(MOAIGeometry2DDeck)
	
	REGISTER_LUA_CLASS(MOAIViewPinTransform)

	REGISTER_LUA_CLASS(MOAIGfxMaskedQuadListDeck2D)
	REGISTER_LUA_CLASS(MOAIGfxMaskedQuadListDeck2DInstance)

	// node helper
	REGISTER_LUA_CLASS(MOAIAttrProcessingNode)

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

	REGISTER_LUA_CLASS(MOAIJoystickManagerSDL)
	MOAIJoystickManagerSDL::Affirm();
	//
	
	REGISTER_LUA_CLASS(MOCKProp)
	REGISTER_LUA_CLASS(EWProp)
	REGISTER_LUA_CLASS(EWPropRenderTransform)
	REGISTER_LUA_CLASS(EWDeckCanvasProp)
	REGISTER_LUA_CLASS(EWBox2DBody)
	REGISTER_LUA_CLASS(EWBox2DWorld)
	REGISTER_LUA_CLASS(EWGrid)
	REGISTER_LUA_CLASS(EWBox2DFixture)

	REGISTER_LUA_CLASS(MOAIMultiShader)

	REGISTER_LUA_CLASS(MOCKPolyPath)
	REGISTER_LUA_CLASS(MOCKPolyClipper)
	REGISTER_LUA_CLASS(MOCKPolyPartition)
	REGISTER_LUA_CLASS(MOCKNavMesh)
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

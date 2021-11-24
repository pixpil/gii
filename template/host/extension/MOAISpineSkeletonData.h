#ifndef	MOAISPINESKELETONDATA_H
#define	MOAISPINESKELETONDATA_H

#include <moai-core/headers.h>
#include <moai-sim/headers.h>

#include <spine/spine.h>
#include <spine/extension.h>

#include "MOAISpineSkeleton.h"
// #include "MOAISpineRegionAttachmentDeck.h"
// #include "MOAISpineMeshAttachmentDeck.h"

//----------------------------------------------------------------//
class MOAISpineAnimationState;


//----------------------------------------------------------------//
class MOAISpineSkeletonData:
	public virtual MOAILuaObject
{
	private:

		friend class MOAISpineSkeleton;
		friend class MOAISpineSkeletonBase;
		friend class MOAISpineAnimationState;

		static int _load               ( lua_State* L );
		static int _loadWithAtlas      ( lua_State* L );
		static int _loadFromString     ( lua_State* L );
		static int _getSkinNames       ( lua_State* L );
		static int _getBoneNames       ( lua_State* L );
		static int _getSlotNames       ( lua_State* L );
		static int _getAnimationNames  ( lua_State* L );
		static int _getEventNames      ( lua_State* L );
		static int _getChildBones      ( lua_State* L );

		static int _getAnimationDuration ( lua_State* L );

	protected:
		SkeletonData* mData  ;
		Atlas*        mAtlas ;

		typedef STLMap < RegionAttachment*, MOAIDeck* >::iterator DeckMapIt;
		STLMap < RegionAttachment*, MOAIDeck* > mAttachmentDeckMap ;
		
	public:
		DECL_LUA_FACTORY( MOAISpineSkeletonData )

		MOAISpineSkeletonData();
		~MOAISpineSkeletonData();

		void RegisterLuaClass ( MOAILuaState& state );
		void RegisterLuaFuncs ( MOAILuaState& state );

		bool Load          ( const char* skelFile, const char* atlasFile );
		bool LoadWithAtlas ( const char* skelFile, Atlas* atlas );
		MOAIDeck* GetAtlasDeck( const char* name );

		Animation* FindAnimation( const char* name );
};

#endif
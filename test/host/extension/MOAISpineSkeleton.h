#ifndef	MOAISPINESKELETON_H
#define	MOAISPINESKELETON_H

#include <moai-core/pch.h>
#include <moai-core/MOAILogMessages.h>

#include <moai-sim/pch.h>
#include <moai-sim/MOAIPartition.h>
#include <moai-sim/MOAIGraphicsProp.h>

#include <spine/spine.h>

#include "MOAISpineAtlas.h"
#include "MOAISpineSkeletonData.h"

class MOAISpineSkeletonData;
class MOAISpineSkeletonBase;
class MOAISpineSkeleton;
class MOAISpineAnimationState;
class MOAISpineAnimation;
class MOAISpineAnimationTrack;

//----------------------------------------------------------------//
class MOAISpineBoneHandle:
	public virtual MOAITransform
{
private:
	friend class MOAISpineSkeleton;
	Bone *mBone;
	u32 mLockFlags;
	enum {
		LOCK_LOC       = 0x01,
		LOCK_ROT       = 0x02,
		LOCK_SCL       = 0x04
	};
	void SyncTransform        ();
	void UpdateTimelineFilter ();

};

//----------------------------------------------------------------//
class MOAISpineSkeletonBase:
	public virtual MOAIGraphicsProp
{
	private:
		friend class MOAISpineAnimationState;
		friend class MOAISpineAnimationTrack;
		friend class MOAISpineAnimation;

		static int _load                  ( lua_State* L );
		static int _unload                ( lua_State* L );
		static int _getSkeletonData       ( lua_State* L );
		//
		static int _setSkin               ( lua_State* L );
		static int _setAttachment         ( lua_State* L );
		//
		static int _setBoneRot            ( lua_State* L );
		static int _setBoneLoc            ( lua_State* L );
		static int _setBoneScl            ( lua_State* L );
		static int _getBoneRot            ( lua_State* L );
		static int _getBoneLoc            ( lua_State* L );
		static int _getBoneScl            ( lua_State* L );
		static int _getBoneLength         ( lua_State* L );
		static int _getBoneParentName     ( lua_State* L );
		static int _getSlotBoneName       ( lua_State* L );
		// static int _setBoneTransform      ( lua_State* L );
		static int _setToSetupPose        ( lua_State* L );
		static int _setBonesToSetupPose   ( lua_State* L );
		static int _setSlotsToSetupPose   ( lua_State* L );
		static int _updateSpine           ( lua_State* L );
		
		void DrawRegionAttachment         ( Slot* slot );
		void DrawMeshAttachment           ( Slot* slot );
		void DrawSkinnedMeshAttachment    ( Slot* slot );

	protected:
		Skeleton* mSkeleton;
		Bone*     mRootBone;

		MOAILuaSharedPtr < MOAISpineSkeletonData > mData;

	public:
		DECL_LUA_FACTORY( MOAISpineSkeletonBase )

		MOAISpineSkeletonBase();
		~MOAISpineSkeletonBase();

		void RegisterLuaClass		( MOAILuaState& state );
		void RegisterLuaFuncs		( MOAILuaState& state );

		//
		void      Load                   ( MOAISpineSkeletonData* data, float ZScale, bool useAlphaBlend = false );
		void      Unload                 ();

		virtual void OnLoad              ( MOAISpineSkeletonData* data, float ZScale );
		virtual void OnUnload            ();
		virtual void UpdateSpine         ();

		void      SetToSetupPose         ();
		void      SetBonesToSetupPose    ();
		void      SetSlotsToSetupPose    ();

		void      SetSkin                ( const char* skinName );
		void      SetAttachment          ( const char* slotName, const char* attachmentName );

};



//----------------------------------------------------------------//
class MOAISpineSkeletonSimple:
	public virtual MOAISpineSkeletonBase
{	
	private:
		void Draw ( int subPrimID, float lod );
		void DrawSpineSlot  ( Slot* slot );
		
		u32 OnGetModelBounds  ( ZLBox& bounds );
		
	public:
		DECL_LUA_FACTORY( MOAISpineSkeletonSimple )

		MOAISpineSkeletonSimple();
		~MOAISpineSkeletonSimple();

		void RegisterLuaClass		( MOAILuaState& state );
		void RegisterLuaFuncs		( MOAILuaState& state );				
};


//----------------------------------------------------------------//
class MOAISpineSlot:
	public virtual MOAIGraphicsProp
{
	private:
		friend class MOAISpineSkeleton;
		// friend class MOAISpineBoneHandle;

		static int _lockVisible    ( lua_State* L );
		static int _lockAttachment ( lua_State* L );
		static int _lockColor      ( lua_State* L );
		static int _lockTransform  ( lua_State* L );

		static int _getName              ( lua_State* L );
		static int _getBoneName           ( lua_State* L );
		static int _getBoneParentName     ( lua_State* L );
		static int _setBoneRot            ( lua_State* L );
		static int _setBoneLoc            ( lua_State* L );
		static int _setBoneScl            ( lua_State* L );
		static int _getBoneRot            ( lua_State* L );
		static int _getBoneLoc            ( lua_State* L );
		static int _getBoneScl            ( lua_State* L );
		static int _getBoneWorldRot       ( lua_State* L );
		static int _getBoneWorldLoc       ( lua_State* L );
		static int _getBoneWorldScl       ( lua_State* L );
		static int _getBoneLength         ( lua_State* L );

		u32 mLockFlags;
		Slot *mSlot;
		MOAISpineSkeleton *mParentSkeleton;

		enum {
			LOCK_VISIBLE	  = 0x01,
			LOCK_ATTACHMENT = 0x02,
			LOCK_COLOR		  = 0x04,
			LOCK_LOC        = 0x08,
			LOCK_SCL        = 0x10,
			LOCK_ROT        = 0x20,
			LOCK_FFD        = 0x40,
		};

		u32 OnGetModelBounds  ( ZLBox& bounds );
		u32 GetAttachmentBounds  ( ZLBox& bounds );

		void DrawRegionAttachment ();
		void DrawMeshAttachment ();
		void DrawSkinnedMeshAttachment ();

		void UpdateTimelineFilter ();


	public:
		void SetDeck          ( MOAIDeck* deck );
		void SetAdditiveBlend ();
		void SetAlphaBlend    ();
		void SetNormalBlend   ();
		void Draw             ( int subPrimID, float lod );
		void SetSlot          ( Slot* slot );

		DECL_LUA_FACTORY ( MOAISpineSlot )

		MOAISpineSlot();
		~MOAISpineSlot();

		void  RegisterLuaClass ( MOAILuaState& state );
		void  RegisterLuaFuncs ( MOAILuaState& state );

};



//----------------------------------------------------------------//
class MOAISpineSkeleton:
	public MOAISpineSkeletonBase
{
	private:
		
		friend class MOAISpineAnimationState;
		friend class MOAISpineAnimationTrack;
		friend class MOAISpineAnimation;
		friend class MOAISpineSlot;

		static int _getSlotProps          ( lua_State* L );
		static int _findSlotProp          ( lua_State* L );
		static int _requestBoneHandle     ( lua_State* L );
		static int _forceUpdateSlots       ( lua_State* L );

		//bone handles
		typedef STLMap < Bone*, MOAISpineBoneHandle* >::iterator BoneHandleIt;
		STLMap < Bone*, MOAISpineBoneHandle* > mBoneHandleMap;

		MOAISpineBoneHandle* RequestBoneHandle( const char* boneName );

	protected:
		typedef STLMap < Slot*, MOAISpineSlot* >::iterator SlotPropIt;
		STLMap < Slot*, MOAISpineSlot* > mSlotPropMap;
		
	public:
		DECL_LUA_FACTORY( MOAISpineSkeleton )

		MOAISpineSkeleton();
		~MOAISpineSkeleton();

		void RegisterLuaClass		( MOAILuaState& state );
		void RegisterLuaFuncs		( MOAILuaState& state );
		
		void OnLoad              ( MOAISpineSkeletonData* data, float ZScale );
		void OnUnload            ();
		void UpdateSpine         ();

		MOAISpineSlot* FindSlotProp           ( const char* slotName );
};



#endif
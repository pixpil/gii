#ifndef MOAIIMGUI_H
#define MOAIIMGUI_H
#endif

#include "moai-sim/headers.h"
#include "moai-imgui/imgui/imgui.h"

//----------------------------------------------------------------//
class MOAIImGui :
	public MOAIGraphicsProp {

private:
	//functions defined in cpp
	static int _init                 ( lua_State* L );
	static int _setSize              ( lua_State* L );
	static int _sendKeyEvent         ( lua_State* L );
	static int _sendTextEvent        ( lua_State* L );
	static int _sendMouseMoveEvent   ( lua_State* L );
	static int _sendMouseButtonEvent ( lua_State* L );
	static int _sendMouseWheelEvent  ( lua_State* L );
	static int _setCallback          ( lua_State* L );

	ImGuiContext* mContext;
	double    mPreviousTime;
	ZLVec2D   mSize;

	bool      mDeviceObjectReady;
	MOAIShader*         mImGuiShader;
	MOAIImageTexture*   mImGuiTexture;

	MOAIVertexFormat* mVertexFormat;
	u32   mVboHandle;
	u32   mElementsHandle;

	MOAILuaMemberRef		mOnFrame;

	bool            MakeCurrent ();
	bool            IsCurrent   ();
	ImGuiIO&        GetIO       ();
	virtual u32     OnGetModelBounds ( ZLBox& bounds ); // get the prop bounds in model space
	
	void            CreateDeviceObjects ();
	void            NewFrame ();

public:

	GET ( ZLVec2D, Size, mSize )

	DECL_LUA_FACTORY ( MOAIImGui )

	MOAIImGui  ();
	~MOAIImGui ();

	void      Init ();

	void			RegisterLuaClass	(MOAILuaState& state);
	void			RegisterLuaFuncs	(MOAILuaState& state);

	virtual void		Draw					( int subPrimID, float lod );

};
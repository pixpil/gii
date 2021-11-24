#include "MOAIImGui.h"

#include <vector>
#include <cstring>

#include "moai-imgui/imgui/imgui.h"
#include "moai-imgui/imgui/imgui_internal.h"


//----------------------------------------------------------------//
#define SHADER(str) #str

static cc8* _imguiShaderVSH = SHADER (

	uniform mat4 transform;

	attribute vec2 position;
	attribute vec2 uv;
	attribute vec4 color;

	varying MEDP vec2 uvVarying;
	varying LOWP vec4 colorVarying;

	void main () {
		uvVarying = uv;
		colorVarying = color;
		gl_Position = vec4( position, 0.0, 1.0 ) * transform;
	}
);

//----------------------------------------------------------------//
static cc8* _imguiShaderFSH = SHADER (

	uniform sampler2D sampler;

	varying LOWP vec4 colorVarying;
	varying MEDP vec2 uvVarying;

	void main() {
		gl_FragColor = texture2D ( sampler, uvVarying ) * colorVarying;
	}
);


//----------------------------------------------------------------//
//----------------------------------------------------------------//
int MOAIImGui::_setSize ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIImGui, "UNN" )
	float w = state.GetValue < float >( 2, 0.0f );
	float h = state.GetValue < float >( 3, 0.0f );
	self->mSize.Init( w, h );
	return 0;
}


//----------------------------------------------------------------//
int MOAIImGui::_sendKeyEvent ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIImGui, "UNB" )
	u32  key      = state.GetValue < u32  >( 2, 0 );
	bool down     = state.GetValue < bool >( 3, true );
	self->GetIO().KeysDown[ key ] = down;
	// io.KeyShift = ((SDL_GetModState() & KMOD_SHIFT) != 0);
	// io.KeyCtrl = ((SDL_GetModState() & KMOD_CTRL) != 0);
	// io.KeyAlt = ((SDL_GetModState() & KMOD_ALT) != 0);
	// io.KeySuper = ((SDL_GetModState() & KMOD_GUI) != 0);
	return 0;
}

//----------------------------------------------------------------//
int MOAIImGui::_sendTextEvent ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIImGui, "US" )
	cc8*  text  = state.GetValue < cc8*  >( 2, "" );
	self->GetIO().AddInputCharactersUTF8( text );
	return 0;
}



int MOAIImGui::_sendMouseMoveEvent ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIImGui, "UNN" )
	ImGuiIO& io = self->GetIO();
	float x  = state.GetValue < float >( 2, 0.0f );
	float y  = state.GetValue < float >( 3, 0.0f );
	self->GetIO().MousePos = ImVec2( x, y );
	return 0;
}

int MOAIImGui::_sendMouseButtonEvent ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIImGui, "UNB" )
	u32 button    = state.GetValue < u32 >( 2, 0 );
	bool down     = state.GetValue < bool >( 3, false );
	if ( button <= 2 ) {
		self->GetIO().MouseDown[ button ] = down;
	}
	return 0;
}

int MOAIImGui::_sendMouseWheelEvent ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIImGui, "UN" )
	float delta = state.GetValue < float >( 2, 0.0f );
	self->GetIO().MouseWheel = delta;
	return 0;
}

int MOAIImGui::_setCallback ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIImGui, "UF" );

	self->mOnFrame.SetRef ( *self, state, 2 );
	return 0;
}

int MOAIImGui::_init ( lua_State* L ) {
	MOAI_LUA_SETUP ( MOAIImGui, "U" );

	self->Init ();
	return 0;
}

#include "moai-imgui/imgui_impl.cpp.inc"


void MOAIImGui::RegisterLuaClass ( MOAILuaState& state ) {

	MOAIGraphicsProp::RegisterLuaClass( state );

	// Enums not handled by iterator yet
	state.SetField( -1, "WindowFlags_NoTitleBar",            ImGuiWindowFlags_NoTitleBar            );
	state.SetField( -1, "WindowFlags_NoResize",              ImGuiWindowFlags_NoResize              );
	state.SetField( -1, "WindowFlags_NoMove",                ImGuiWindowFlags_NoMove                );
	state.SetField( -1, "WindowFlags_NoScrollbar",           ImGuiWindowFlags_NoScrollbar           );
	state.SetField( -1, "WindowFlags_NoScrollWithMouse",     ImGuiWindowFlags_NoScrollWithMouse     );
	state.SetField( -1, "WindowFlags_NoCollapse",            ImGuiWindowFlags_NoCollapse            );
	state.SetField( -1, "WindowFlags_AlwaysAutoResize",      ImGuiWindowFlags_AlwaysAutoResize      );
	state.SetField( -1, "WindowFlags_ShowBorders",           ImGuiWindowFlags_ShowBorders           );
	state.SetField( -1, "WindowFlags_NoSavedSettings",       ImGuiWindowFlags_NoSavedSettings       );
	state.SetField( -1, "WindowFlags_NoInputs",              ImGuiWindowFlags_NoInputs              );
	state.SetField( -1, "WindowFlags_MenuBar",               ImGuiWindowFlags_MenuBar               );
	state.SetField( -1, "WindowFlags_HorizontalScrollbar",   ImGuiWindowFlags_HorizontalScrollbar   );
	state.SetField( -1, "WindowFlags_NoFocusOnAppearing",    ImGuiWindowFlags_NoFocusOnAppearing    );
	state.SetField( -1, "WindowFlags_NoBringToFrontOnFocus", ImGuiWindowFlags_NoBringToFrontOnFocus );
	state.SetField( -1, "WindowFlags_ChildWindow",           ImGuiWindowFlags_ChildWindow           );
	state.SetField( -1, "WindowFlags_ChildWindowAutoFitX",   ImGuiWindowFlags_ChildWindowAutoFitX   );
	state.SetField( -1, "WindowFlags_ChildWindowAutoFitY",   ImGuiWindowFlags_ChildWindowAutoFitY   );
	state.SetField( -1, "WindowFlags_ComboBox",              ImGuiWindowFlags_ComboBox              );
	state.SetField( -1, "WindowFlags_Tooltip",               ImGuiWindowFlags_Tooltip               );
	state.SetField( -1, "WindowFlags_Popup",                 ImGuiWindowFlags_Popup                 );
	state.SetField( -1, "WindowFlags_Modal",                 ImGuiWindowFlags_Modal                 );
	state.SetField( -1, "WindowFlags_ChildMenu",             ImGuiWindowFlags_ChildMenu             );

	state.SetField( -1, "TreeNodeFlags_Selected",              ImGuiTreeNodeFlags_Selected            );
	state.SetField( -1, "TreeNodeFlags_Framed",                ImGuiTreeNodeFlags_Framed              );
	state.SetField( -1, "TreeNodeFlags_AllowOverlapMode",      ImGuiTreeNodeFlags_AllowOverlapMode    );
	state.SetField( -1, "TreeNodeFlags_NoTreePushOnOpen",      ImGuiTreeNodeFlags_NoTreePushOnOpen    );
	state.SetField( -1, "TreeNodeFlags_NoAutoOpenOnLog",       ImGuiTreeNodeFlags_NoAutoOpenOnLog     );
	state.SetField( -1, "TreeNodeFlags_DefaultOpen",           ImGuiTreeNodeFlags_DefaultOpen         );
	state.SetField( -1, "TreeNodeFlags_OpenOnDoubleClick",     ImGuiTreeNodeFlags_OpenOnDoubleClick   );
	state.SetField( -1, "TreeNodeFlags_OpenOnArrow",           ImGuiTreeNodeFlags_OpenOnArrow         );
	state.SetField( -1, "TreeNodeFlags_Leaf",                  ImGuiTreeNodeFlags_Leaf                );
	state.SetField( -1, "TreeNodeFlags_Bullet",                ImGuiTreeNodeFlags_Bullet              );

	state.SetField( -1, "InputTextFlags_CharsDecimal",          ImGuiInputTextFlags_CharsDecimal       );
	state.SetField( -1, "InputTextFlags_CharsHexadecimal",      ImGuiInputTextFlags_CharsHexadecimal   );
	state.SetField( -1, "InputTextFlags_CharsUppercase",        ImGuiInputTextFlags_CharsUppercase     );
	state.SetField( -1, "InputTextFlags_CharsNoBlank",          ImGuiInputTextFlags_CharsNoBlank       );
	state.SetField( -1, "InputTextFlags_AutoSelectAll",         ImGuiInputTextFlags_AutoSelectAll      );
	state.SetField( -1, "InputTextFlags_EnterReturnsTrue",      ImGuiInputTextFlags_EnterReturnsTrue   );
	state.SetField( -1, "InputTextFlags_CallbackCompletion",    ImGuiInputTextFlags_CallbackCompletion );
	state.SetField( -1, "InputTextFlags_CallbackHistory",       ImGuiInputTextFlags_CallbackHistory    );
	state.SetField( -1, "InputTextFlags_CallbackAlways",        ImGuiInputTextFlags_CallbackAlways     );
	state.SetField( -1, "InputTextFlags_CallbackCharFilter",    ImGuiInputTextFlags_CallbackCharFilter );
	state.SetField( -1, "InputTextFlags_AllowTabInput",         ImGuiInputTextFlags_AllowTabInput      );
	state.SetField( -1, "InputTextFlags_CtrlEnterForNewLine",   ImGuiInputTextFlags_CtrlEnterForNewLine);
	state.SetField( -1, "InputTextFlags_NoHorizontalScroll",    ImGuiInputTextFlags_NoHorizontalScroll );
	state.SetField( -1, "InputTextFlags_AlwaysInsertMode",      ImGuiInputTextFlags_AlwaysInsertMode   );
	state.SetField( -1, "InputTextFlags_ReadOnly",              ImGuiInputTextFlags_ReadOnly           );
	state.SetField( -1, "InputTextFlags_Password",              ImGuiInputTextFlags_Password           );
	state.SetField( -1, "InputTextFlags_Multiline",             ImGuiInputTextFlags_Multiline          );

	state.SetField( -1, "SelectableFlags_DontClosePopups",       ImGuiSelectableFlags_DontClosePopups   );
	state.SetField( -1, "SelectableFlags_SpanAllColumns",        ImGuiSelectableFlags_SpanAllColumns    );
	
	state.SetField( -1, "Key_Tab",               ImGuiKey_Tab                           );
	state.SetField( -1, "Key_LeftArrow",         ImGuiKey_LeftArrow                     );
	state.SetField( -1, "Key_RightArrow",        ImGuiKey_RightArrow                    );
	state.SetField( -1, "Key_UpArrow",           ImGuiKey_UpArrow                       );
	state.SetField( -1, "Key_DownArrow",         ImGuiKey_DownArrow                     );
	state.SetField( -1, "Key_PageUp",            ImGuiKey_PageUp                        );
	state.SetField( -1, "Key_PageDown",          ImGuiKey_PageDown                      );
	state.SetField( -1, "Key_Home",              ImGuiKey_Home                          );
	state.SetField( -1, "SetCond_Always",        ImGuiSetCond_Always                    );
	state.SetField( -1, "SetCond_Once",          ImGuiSetCond_Once                      );
	state.SetField( -1, "SetCond_FirstUseEver",  ImGuiSetCond_FirstUseEver              );
	state.SetField( -1, "SetCond_Appearing",     ImGuiSetCond_Appearing                 );
}


//----------------------------------------------------------------//
void MOAIImGui::RegisterLuaFuncs( MOAILuaState& state )
{
	
	MOAIGraphicsProp::RegisterLuaFuncs( state );

	luaL_Reg regTable [] = {
	#include "moai-imgui/imgui_impl_reg.cpp.inc"
		{ "init",                 _init                 },
		{ "setSize",              _setSize              },
		{ "sendKeyEvent",         _sendKeyEvent         },
		{ "sendTextEvent",        _sendTextEvent        },
		{ "sendMouseWheelEvent",  _sendMouseWheelEvent  },
		{ "sendMouseMoveEvent",   _sendMouseMoveEvent   },
		{ "sendMouseButtonEvent", _sendMouseButtonEvent },
		{ "sendMouseWheelEvent",  _sendMouseWheelEvent  },
		{ "setCallback",          _setCallback          },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}


//----------------------------------------------------------------//
MOAIImGui::MOAIImGui () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIGraphicsProp )
	RTTI_END
	
	this->mDeviceObjectReady = false;

	this->mContext = ImGui::CreateContext ();
	this->mPreviousTime = -1.0;
	this->mImGuiShader = NULL;
	this->mImGuiTexture = NULL;
	this->mSize.Init ( 0.0f, 0.0f );
	this->mContext->IO.RenderDrawListsFn  = NULL;
	this->mContext->IO.SetClipboardTextFn = NULL;
	this->mContext->IO.GetClipboardTextFn = NULL;

	this->mBlendMode.SetBlend ( ZGL_BLEND_FACTOR_SRC_ALPHA, ZGL_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA );

}

MOAIImGui::~MOAIImGui () {
	this->MakeCurrent ();
	//remove
	if ( this->mDeviceObjectReady ) {
		MOAIGfxResourceMgr::Get ().PushDeleter ( MOAIGfxDeleter::DELETE_BUFFER, this->mVboHandle );
		MOAIGfxResourceMgr::Get ().PushDeleter ( MOAIGfxDeleter::DELETE_BUFFER, this->mElementsHandle );
		this->LuaRelease ( this->mImGuiTexture );
		this->LuaRelease ( this->mVertexFormat );
		this->LuaRelease ( this->mImGuiShader );
	}

	// ImGui::DestroyContext ( this->mContext );
	// ImGui::Shutdown (); //TODO
}


//----------------------------------------------------------------//
//----------------------------------------------------------------//
u32 MOAIImGui::OnGetModelBounds ( ZLBox& bounds ) {
	return BOUNDS_GLOBAL;
}

//----------------------------------------------------------------//
bool MOAIImGui::MakeCurrent () {
	ImGui::SetCurrentContext( this->mContext );
	return true;
}

//----------------------------------------------------------------//
bool MOAIImGui::IsCurrent () {
	return ImGui::GetCurrentContext() == this->mContext;
}

//----------------------------------------------------------------//
ImGuiIO& MOAIImGui::GetIO () {
	return this->mContext->IO;
}

//----------------------------------------------------------------//
void MOAIImGui::CreateDeviceObjects () {
	if ( this->mDeviceObjectReady ) return ;

	zglBegin();
	// Build texture atlas
	ImGuiIO& io = ImGui::GetIO ();
	unsigned char* pixels;
	int width, height;
	io.Fonts->GetTexDataAsRGBA32 ( &pixels, &width, &height );

	MOAIImageTexture* texture = new MOAIImageTexture ();
	texture->Init ( pixels, width, height, ZLColor::RGBA_8888 );
	texture->SetWrap ( true );
	texture->SetFilter ( ZGL_SAMPLE_LINEAR );
	this->mImGuiTexture = texture;
	this->LuaRetain( texture );

	// //VBO
	this->mVboHandle      = zglCreateBuffer ();
	this->mElementsHandle = zglCreateBuffer ();

	MOAIVertexFormat* format = new MOAIVertexFormat ();
	this->LuaRetain ( format );
	format->DeclareAttribute ( 0, ZGL_TYPE_FLOAT, 2, MOAIVertexFormat::ARRAY_VERTEX, false );
	format->DeclareAttribute ( 1, ZGL_TYPE_FLOAT, 2, MOAIVertexFormat::ARRAY_TEX_COORD, false );
	format->DeclareAttribute ( 2, ZGL_TYPE_UNSIGNED_BYTE, 4, MOAIVertexFormat::ARRAY_COLOR, true );
	this->mVertexFormat = format;

	// Store our identifier
	io.Fonts->TexID = texture;

	//build shader
	MOAIShaderProgram* program = new MOAIShaderProgram ();

	program->SetSource ( _imguiShaderVSH, _imguiShaderFSH );
	program->SetVertexAttribute ( 0, "position" );
	program->SetVertexAttribute ( 1, "uv" );
	program->SetVertexAttribute ( 2, "color" );

	program->ReserveUniforms ( 1 );
	program->DeclareUniform ( 0, "transform", MOAIShaderUniform::UNIFORM_MATRIX_F4 );

	program->ReserveGlobals ( 1 );
	program->SetGlobal ( 0, 0, MOAIShaderProgram::GLOBAL_WORLD_VIEW_PROJ );

	MOAIShader* shader = new MOAIShader ();
	shader->SetProgram ( program );

	this->LuaRetain ( shader );
	this->mImGuiShader = shader;

	this->mDeviceObjectReady = true;
	zglEnd();
}


//----------------------------------------------------------------//
void MOAIImGui::Init () {
	this->CreateDeviceObjects ();
}

//----------------------------------------------------------------//
void MOAIImGui::NewFrame () {
	this->MakeCurrent ();
	ImGuiIO& io = ImGui::GetIO ();

	io.DisplaySize = ImVec2( this->mSize.mX, this->mSize.mY );
	io.DisplayFramebufferScale = ImVec2( 1.0f, 1.0f );

	ImGui::NewFrame ();
	io.MouseWheel = 0;

	if ( this->mOnFrame ) {

		MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();
		if ( this->mOnFrame.PushRef ( state )) {
			this->PushLuaUserdata( state );
			state.DebugCall ( 1, 0 );
		}

		// int count = ImGui::GetFrameCount ();
	}

}

//----------------------------------------------------------------//
void MOAIImGui::Draw ( int subPrimID, float lod ) {
	UNUSED ( subPrimID );

	if ( !this->IsVisible ( lod ) ) return;
	if ( !this->MakeCurrent () ) return;
	if ( !this->mDeviceObjectReady ) return;
	//newframe
	this->NewFrame ();

	double currentTime = MOAISim::Get ().GetSimTime ();
	if ( this->mPreviousTime < 0.0f ) {
		this->GetIO().DeltaTime = 0.0f;
	} else {
		this->GetIO().DeltaTime = currentTime - this->mPreviousTime;
	}
	this->mPreviousTime = currentTime;

	MOAIGfxDevice& gfxDevice = MOAIGfxDevice::Get();
	ImGuiIO& io = ImGui::GetIO();

	ImGui::Render ();

	gfxDevice.Flush ();

	this->LoadGfxState ();
	this->LoadVertexTransform ();

	gfxDevice.SetVertexMtxMode ( MOAIGfxDevice::VTX_STAGE_MODEL, MOAIGfxDevice::VTX_STAGE_MODEL );
	gfxDevice.SetUVMtxMode ( MOAIGfxDevice::UV_STAGE_MODEL, MOAIGfxDevice::UV_STAGE_TEXTURE );

	gfxDevice.SetShader ( this->mImGuiShader );
	gfxDevice.UpdateShaderGlobals ();

	zglBegin ();

	// Avoid rendering when minimized, scale coordinates for retina displays (screen coordinates != framebuffer coordinates)
	ImDrawData* drawData = ImGui::GetDrawData ();

	int fb_width = (int)(io.DisplaySize.x * io.DisplayFramebufferScale.x);
	int fb_height = (int)(io.DisplaySize.y * io.DisplayFramebufferScale.y);
	if (fb_width == 0 || fb_height == 0 || (!drawData) ) {
		zglEnd ();
		gfxDevice.ResetState ();
		return;
	}

	drawData->ScaleClipRects( io.DisplayFramebufferScale );
	zglBindBuffer( ZGL_BUFFER_TARGET_ARRAY, this->mVboHandle );
	this->mVertexFormat->Bind ( 0 );
	zglBindBuffer( ZGL_BUFFER_TARGET_ELEMENT_ARRAY, this->mElementsHandle );
	ZLRect scissor;
	for (int n = 0; n < drawData->CmdListsCount; n++)
	{
		const ImDrawList* cmd_list = drawData->CmdLists[n];
		const ImDrawIdx* idx_buffer_offset = 0;

		zglBufferData( ZGL_BUFFER_TARGET_ARRAY, 
			cmd_list->VtxBuffer.size() * sizeof(ImDrawVert), 
			&cmd_list->VtxBuffer.front(),
			ZGL_BUFFER_USAGE_STREAM_DRAW
		);

		zglBufferData( ZGL_BUFFER_TARGET_ELEMENT_ARRAY, 
			cmd_list->IdxBuffer.size() * sizeof(ImDrawIdx), 
			&cmd_list->IdxBuffer.front(),
			ZGL_BUFFER_USAGE_STREAM_DRAW
		);

		for (const ImDrawCmd* pcmd = cmd_list->CmdBuffer.begin(); pcmd != cmd_list->CmdBuffer.end(); pcmd++)
		{
			if (pcmd->UserCallback)
			{
				pcmd->UserCallback(cmd_list, pcmd);
			}
			else
			{
				gfxDevice.SetTexture( (MOAIImageTexture*)pcmd->TextureId );
				scissor.Init ( pcmd->ClipRect.x, pcmd->ClipRect.y, pcmd->ClipRect.z, pcmd->ClipRect.w );
				gfxDevice.SetScissorRect( scissor );
				zglDrawElements(
					ZGL_PRIM_TRIANGLES, 
					pcmd->ElemCount,
					sizeof(ImDrawIdx) == 2 ? ZGL_TYPE_UNSIGNED_SHORT : ZGL_TYPE_UNSIGNED_INT,
					idx_buffer_offset
				);
			}
			idx_buffer_offset += pcmd->ElemCount;
		}
	}

	zglBindBuffer ( ZGL_BUFFER_TARGET_ARRAY, 0 ); // OK?
	zglBindBuffer ( ZGL_BUFFER_TARGET_ELEMENT_ARRAY, 0 ); // OK?
	this->mVertexFormat->Unbind ();
	
	zglEnd ();

}


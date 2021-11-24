//----------------------------------------------------------------//
//----------------------------------------------------------------//
#define IMGUI_FUNCTION(name) \
static int impl_##name(lua_State *L) { \
	int max_args = lua_gettop(L); \
	int arg = 1; \
	int stackval = 0;

#define OPTIONAL_LABEL_ARG(name, value) \
	const char* name; \
	if (arg <= max_args) { \
		name = lua_tostring(L, arg++); \
				} else { \
		name = value; \
				}

#define LABEL_ARG(name) \
	size_t i_##name##_size; \
	const char * name = luaL_checklstring(L, arg++, &(i_##name##_size));

#define LABEL_POINTER_ARG(name) \
	size_t i_##name##_size; \
	const char * content = luaL_checklstring(L, arg++, &(i_##name##_size)); \
	size_t buf_size = luaL_checknumber(L, arg++); \
	char * name = new char [buf_size]; \
	std::strcpy(name, content);

#define END_LABEL_POINTER(name) \
	if (name != NULL) { \
		lua_pushstring(L, name); \
	delete[] name; \
		stackval++; \
			}

#define LABEL_ARRAY_ARG(name) \
	luaL_checktype(L, arg, LUA_TTABLE); \
	int len = lua_objlen(L, arg++); \
	std::vector<const char *> list; \
	for (int i = 0; i < len; i++) \
	{ \
	lua_pushinteger(L, i + 1); \
	lua_gettable(L, arg - 1); \
	size_t current_size; \
	list.push_back(luaL_checklstring(L, -1, &(current_size))); \
	} \
	const char **name = list.data(); \

#define IM_VEC_2_ARG(name)\
	const lua_Number i_##name##_x = luaL_checknumber(L, arg++); \
	const lua_Number i_##name##_y = luaL_checknumber(L, arg++); \
	const ImVec2 name((double)i_##name##_x, (double)i_##name##_y);

#define OPTIONAL_IM_VEC_2_ARG(name, x, y) \
	lua_Number i_##name##_x = x; \
	lua_Number i_##name##_y = y; \
	if (arg <= max_args - 1) { \
		i_##name##_x = luaL_checknumber(L, arg++); \
		i_##name##_y = luaL_checknumber(L, arg++); \
		} \
	const ImVec2 name((double)i_##name##_x, (double)i_##name##_y);

#define IM_VEC_4_ARG(name)\
	const lua_Number i_##name##_x = luaL_checknumber(L, arg++); \
	const lua_Number i_##name##_y = luaL_checknumber(L, arg++); \
	const lua_Number i_##name##_z = luaL_checknumber(L, arg++); \
	const lua_Number i_##name##_w = luaL_checknumber(L, arg++); \
	const ImVec4 name((double)i_##name##_x, (double)i_##name##_y, (double)i_##name##_z, (double)i_##name##_w);

#define OPTIONAL_IM_VEC_4_ARG(name, x, y, z, w) \
	lua_Number i_##name##_x = x; \
	lua_Number i_##name##_y = y; \
	lua_Number i_##name##_z = z; \
	lua_Number i_##name##_w = w; \
	if (arg <= max_args - 1) { \
		i_##name##_x = luaL_checknumber(L, arg++); \
		i_##name##_y = luaL_checknumber(L, arg++); \
		i_##name##_z = luaL_checknumber(L, arg++); \
		i_##name##_w = luaL_checknumber(L, arg++); \
			} \
	const ImVec4 name((double)i_##name##_x, (double)i_##name##_y, (double)i_##name##_z, (double)i_##name##_w);

#define NUMBER_ARG(name)\
	lua_Number name = luaL_checknumber(L, arg++);

#define OPTIONAL_NUMBER_ARG(name, otherwise)\
	lua_Number name = otherwise; \
	if (arg <= max_args) { \
		name = lua_tonumber(L, arg++); \
		}

#define FLOAT_POINTER_ARG(name) \
	float i_##name##_value = luaL_checknumber(L, arg++); \
	float* name = &(i_##name##_value);

#define END_FLOAT_POINTER(name) \
	if (name != NULL) { \
		lua_pushnumber(L, i_##name##_value); \
		stackval++; \
		}

#define FLOAT_ARRAY2_ARG(name) \
	float i_##name##_1 = luaL_checknumber(L, arg++); \
	float i_##name##_2 = luaL_checknumber(L, arg++); \
	float name[2] = { i_##name##_1, i_##name##_2 };

#define END_FLOAT_ARRAY2(name) \
		lua_pushnumber(L, name[0]); \
		lua_pushnumber(L, name[1]); \
		stackval += 2; \

#define FLOAT_ARRAY3_ARG(name) \
	float i_##name##_1 = luaL_checknumber(L, arg++); \
	float i_##name##_2 = luaL_checknumber(L, arg++); \
	float i_##name##_3 = luaL_checknumber(L, arg++); \
	float name[3] = { i_##name##_1, i_##name##_2, i_##name##_3 };

#define END_FLOAT_ARRAY3(name) \
		lua_pushnumber(L, name[0]); \
		lua_pushnumber(L, name[1]); \
		lua_pushnumber(L, name[2]); \
		stackval += 3; \

#define FLOAT_ARRAY4_ARG(name) \
	float i_##name##_1 = luaL_checknumber(L, arg++); \
	float i_##name##_2 = luaL_checknumber(L, arg++); \
	float i_##name##_3 = luaL_checknumber(L, arg++); \
	float i_##name##_4 = luaL_checknumber(L, arg++); \
	float name[4] = { i_##name##_1, i_##name##_2, i_##name##_3, i_##name##_4 };

#define END_FLOAT_ARRAY4(name) \
		lua_pushnumber(L, name[0]); \
		lua_pushnumber(L, name[1]); \
		lua_pushnumber(L, name[2]); \
		lua_pushnumber(L, name[3]); \
		stackval += 4; \

#define INT_ARRAY2_ARG(name) \
	int i_##name##_1 = luaL_checknumber(L, arg++); \
	int i_##name##_2 = luaL_checknumber(L, arg++); \
	int name[2] = { i_##name##_1, i_##name##_2 };

#define END_INT_ARRAY2(name) \
		lua_pushnumber(L, name[0]); \
		lua_pushnumber(L, name[1]); \
		stackval += 2; \

#define INT_ARRAY3_ARG(name) \
	int i_##name##_1 = luaL_checknumber(L, arg++); \
	int i_##name##_2 = luaL_checknumber(L, arg++); \
	int i_##name##_3 = luaL_checknumber(L, arg++); \
	int name[3] = { i_##name##_1, i_##name##_2, i_##name##_3 };

#define END_INT_ARRAY3(name) \
		lua_pushnumber(L, name[0]); \
		lua_pushnumber(L, name[1]); \
		lua_pushnumber(L, name[2]); \
		stackval += 3; \

#define INT_ARRAY4_ARG(name) \
	int i_##name##_1 = luaL_checknumber(L, arg++); \
	int i_##name##_2 = luaL_checknumber(L, arg++); \
	int i_##name##_3 = luaL_checknumber(L, arg++); \
	int i_##name##_4 = luaL_checknumber(L, arg++); \
	int name[4] = { i_##name##_1, i_##name##_2, i_##name##_3, i_##name##_4 };

#define END_INT_ARRAY4(name) \
		lua_pushnumber(L, name[0]); \
		lua_pushnumber(L, name[1]); \
		lua_pushnumber(L, name[2]); \
		lua_pushnumber(L, name[3]); \
		stackval += 4; \

#define OPTIONAL_INT_ARG(name, otherwise)\
	int name = otherwise; \
	if (arg <= max_args) { \
		name = (int)lua_tonumber(L, arg++); \
		}

#define INT_ARG(name) \
	const int name = (int)luaL_checknumber(L, arg++);

#define OPTIONAL_UINT_ARG(name, otherwise)\
	unsigned int name = otherwise; \
	if (arg <= max_args) { \
		name = (unsigned int)lua_tounsigned(L, arg++); \
		}

#define UINT_ARG(name) \
	const unsigned int name = (unsigned int)luaL_checkinteger(L, arg++);

#define INT_POINTER_ARG(name) \
	int i_##name##_value = (int)luaL_checkinteger(L, arg++); \
	int* name = &(i_##name##_value);

#define END_INT_POINTER(name) \
	if (name != NULL) { \
		lua_pushnumber(L, i_##name##_value); \
		stackval++; \
		}

#define UINT_POINTER_ARG(name) \
	unsigned int i_##name##_value = (unsigned int)luaL_checkinteger(L, arg++); \
	unsigned int* name = &(i_##name##_value);

#define END_UINT_POINTER(name) \
	if (name != NULL) { \
		lua_pushnumber(L, i_##name##_value); \
		stackval++; \
		}

#define BOOL_POINTER_ARG(name) \
	bool i_##name##_value = lua_toboolean(L, arg++); \
	bool* name = &(i_##name##_value);

#define OPTIONAL_BOOL_POINTER_ARG(name) \
	bool i_##name##_value; \
	bool* name = NULL; \
	if (arg <= max_args) { \
	if (lua_isboolean(L, arg++)) \
		{ \
			i_##name##_value = lua_toboolean(L, -1); \
			name = &(i_##name##_value); \
	} \
		}

#define OPTIONAL_BOOL_ARG(name, otherwise) \
	bool name = otherwise; \
	if (arg <= max_args) { \
		name = lua_toboolean(L, arg++); \
		}

#define DEFAULT_ARG(type, name, value) \
	type name = value; \

#define BOOL_ARG(name) \
	bool name = lua_toboolean(L, arg++);

#define CALL_FUNCTION(name, retType,...) \
	retType ret = ImGui::name(__VA_ARGS__);

#define CALL_FUNCTION_NO_RET(name,...) \
	ImGui::name(__VA_ARGS__);

#define PUSH_NUMBER(name) \
	lua_pushnumber(L, name); \
	stackval++;

#define PUSH_BOOL(name) \
	lua_pushboolean(L, (int) name); \
	stackval++;

#define END_BOOL_POINTER(name) \
	if (name != NULL) { \
		lua_pushboolean(L, (int)i_##name##_value); \
		stackval++; \
		}

#define END_IMGUI_FUNC \
	return stackval; \
}

#ifdef ENABLE_IM_LUA_END_STACK
#define IF_RET_ADD_END_STACK(type) \
	if (ret) { \
		AddToStack(type); \
		}

#define ADD_END_STACK(type) \
	AddToStack(type);

#define POP_END_STACK(type) \
	PopEndStack(type);

#define END_STACK_START \
static void ImEndStack(int type) { \
	switch(type) {

#define END_STACK_OPTION(type, function) \
		case type: \
			ImGui::function(); \
			break;

#define END_STACK_END \
		} \
}
#else
#define END_STACK_START
#define END_STACK_OPTION(type, function)
#define END_STACK_END
#define IF_RET_ADD_END_STACK(type)
#define ADD_END_STACK(type)
#define POP_END_STACK(type)
#endif

#include "moai-imgui/imgui_iterator.cpp.inc"

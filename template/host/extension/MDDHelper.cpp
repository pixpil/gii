
#include <MDDHelper.h>

#define stackSize 16777216

int stack[stackSize];
int stackPointer=0;

bool pop(int &x, int &y)
{
    if(stackPointer > 1)
    {
        x = stack[stackPointer-2];
        y = stack[stackPointer-1];
        stackPointer-=2;
        return 1;
    }    
    else
    {
        return 0;
    }   
}   
 
bool push(int x, int y)
{
    if(stackPointer < stackSize - 1)
    {
        stack[stackPointer] = x;
        stack[stackPointer+1] = y;
        stackPointer+=2;
        return 1;
    }    
    else
    {
        return 0;
    }   
}    

void emptyStack()
{
    stackPointer=0;
}

#define TILE(x,y) buffer[(x+y*w)]

void fillTiles( ZLLeanArray <u32>& buffer, int w, int h, int x, int y, u32 newColor)
{
		u32 oldColor = TILE(x,y);

    if(oldColor == newColor) return;
    emptyStack();
    
    int y1; //note: if you use y here, we're working vertically. This goes much faster in this case, because reading and writing the buffer[x][y] goes faster if y is incremented/decremented
    bool spanLeft, spanRight;

    if(!push(x, y)) return;
    
    while(pop(x, y))
    {    
        y1 = y;
        while(TILE(x,y1) == oldColor && y1 >= 0) y1--;
        y1++;
        spanLeft = spanRight = 0;
        while(TILE(x,y1) == oldColor && y1 < h)
        {           
            TILE(x,y1) = newColor;
            if(!spanLeft && x > 0 && TILE(x - 1,y1) == oldColor) 
            {
                if(!push(x - 1, y1)) return;
                spanLeft = 1;
            }
            else if(spanLeft && x > 0 && TILE(x - 1,y1) != oldColor)
            {
                spanLeft = 0;
            }
            if(!spanRight && x < w - 1 && TILE(x + 1,y1) == oldColor) 
            {
                if(!push(x + 1, y1)) return;
                spanRight = 1;
            }
            else if(spanRight && x < w - 1 && TILE(x + 1,y1) != oldColor)
            {
                spanRight = 0;
            }                 
            y1++;                    
        }
    }        
}



bool MDDHelper::canSeeCell(MOAIGrid* grid, int x0,int y0,int x1,int y1){
	int dx,dy;
	dx=x1-x0;
	dy=y1-y0;

	if(dx*dx>dy*dy){
		float r=(float)dy/(float)dx;
		int step=dx>0 ? 1: -1;
		int ddx=0;
		int bx=x0,by=y0;

		while(1){
			int x,y;
			x=x0+ddx;
			y=y0+(float)ddx * r;
			if(by!=y){ //avoid diagonal cross
				if(grid->GetTile(bx,y)==0 && grid->GetTile(x,by)==0) return false;
			}

			if(grid->GetTile(x,y)==0) return false;
			if(ddx==dx) break ;
			ddx+=step;
			by=y;
			bx=x;
		}

	}else{
		if(dy==0) return true;
		int step=dy>0 ? 1: -1;
		float r=(float)dx/(float)dy;

		int ddy=0;
		int bx=x0, by=y0;

		while(1){
			int x,y;
			y=y0+ddy;
			x=x0+(float)ddy * r;
			if(bx!=x){ //avoid diagonal cross
				if(grid->GetTile(bx,y)==0 && grid->GetTile(x,by)==0) return false;
			}

			if(grid->GetTile(x,y)==0) return false;
			if (ddy==dy) break;
			ddy+=step;
			bx=x;
			by=y;
		}

	}	
	return true;
}

int MDDHelper::_canSeeCell(lua_State *L){
	MOAILuaState state ( L );
	MOAIGrid* grid=state.GetLuaObject <MOAIGrid> (1, true);
	
	int x0=state.GetValue <int> (2, 1)-1;
	int y0=state.GetValue <int> (3, 1)-1;

	int x1=state.GetValue <int> (4, 1)-1;
	int y1=state.GetValue <int> (5, 1)-1;

	lua_pushboolean(L, canSeeCell(grid, x0,y0,x1,y1));

	return 1;
}

int MDDHelper::_getSeeableCells(lua_State *L){
	MOAILuaState state ( L );
	MOAIGrid* grid=state.GetLuaObject <MOAIGrid> (1, true);
	
	int x=state.GetValue <int> (2, 1)-1;
	int y=state.GetValue <int> (3, 1)-1;

	int range=state.GetValue <int> (4, 3);
	int w=grid->GetWidth(), h=grid->GetHeight();

	int x0,y0,x1,y1;
	x0=x-range; if(x0<0) x0=0;
	y0=y-range; if(y0<0) y0=0;
	x1=x+range; if(x1>=w) x1=w-1;
	y1=y+range; if(y1>=h) y1=h-1;

	int count=0;
	for(int xx=x0; xx<=x1; xx++)
		for(int yy=y0; yy<=y1; yy++)
		{
				int dx=xx-x, dy=yy-y;
				if (dx*dx+dy*dy<=range*range && canSeeCell(grid,xx,yy,x,y)){
					lua_pushnumber(L, grid->GetCellAddr(xx,yy)+1) ;
					count++;
				}
		}

	return count;
}


int MDDHelper::_blockAction(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UU" )) return 0;

	MOAIAction *blocked = state.GetLuaObject<MOAIAction>(1,true);
	MOAIAction *blocker = state.GetLuaObject<MOAIAction>(2,true);

	if(blocked && blocker){
		blocked->SetBlocker(blocker);
	}

	return 0;
}

int MDDHelper::_fillGrid(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UNNN" )) return 0;

	MOAIGrid *grid=state.GetLuaObject<MOAIGrid>(1,true);
	ZLLeanArray<u32>& buffer=grid->GetTileArray();

	u32 x=state.GetValue <u32> (2,1)-1;
	u32 y=state.GetValue <u32> (3,1)-1;

	u32 code=state.GetValue <u32> (4,0);

	u32 w=grid->GetWidth();
	u32 h=grid->GetHeight();
	
	fillTiles(buffer, w,h, x,y, code);
	
	return 0;
}

int MDDHelper::_setTileBit(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UNNN" )) return 0;
	MOAIGrid *grid=state.GetLuaObject<MOAIGrid>(1,true);
	// ZLLeanArray<u32>& buffer=grid->GetTileArray();
	u32 x=state.GetValue <u32> (2,1)-1;
	u32 y=state.GetValue <u32> (3,1)-1;
	
	u32 bit=state.GetValue <u32> (4,1);
	bool value=state.GetValue <bool> (5,0);

	u32 code=grid->GetTile(x,y);

	if(value){
		code |= 1 << (bit-1);
	}else{
		code &= ~(1 << (bit-1));
	}

	grid->SetTile(x,y,code);
	return 0;
}

int MDDHelper::_getTileBit(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UNNN" )) return 0;
	MOAIGrid *grid=state.GetLuaObject<MOAIGrid>(1,true);
	// ZLLeanArray<u32>& buffer=grid->GetTileArray();
	u32 x=state.GetValue <u32> (2,1)-1;
	u32 y=state.GetValue <u32> (3,1)-1;
	
	u32 bit=state.GetValue <u32> (4,1)-1;

	u32 code=grid->GetTile(x,y);
	state.Push( (bool)((code>>bit) & 1) );
	return 1;
}

int MDDHelper::_bitsToTile(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UNN" )) return 0;
	MOAIGrid *grid=state.GetLuaObject<MOAIGrid>(1,true);
	// ZLLeanArray<u32>& buffer=grid->GetTileArray();
	u32 x=state.GetValue <u32> (2,1)-1;
	u32 y=state.GetValue <u32> (3,1)-1;
	int top=state.GetTop();
	u32 code=0;
	for(int i=4;i<=top;i++){
		code|=(state.GetValue<bool>(i, 0) << (i-4));
	}
	grid->SetTile(x,y,code);
	return 0;
}

int MDDHelper::_tileToBits(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UNNN" )) return 0;
	MOAIGrid *grid=state.GetLuaObject<MOAIGrid>(1,true);
	// ZLLeanArray<u32>& buffer=grid->GetTileArray();
	u32 x=state.GetValue <u32> (2,1)-1;
	u32 y=state.GetValue <u32> (3,1)-1;

	u32 code=grid->GetTile(x,y);

	int bitcount=state.GetValue <u32> (4,8);
	for(int i=0; i<bitcount; i++){
		state.Push((bool) (code >> i & 0x1));
	}
	return bitcount;
}


int MDDHelper::_distanceBetweenTransform(lua_State *L){
	MOAILuaState state (L);
	if ( !state.CheckParams ( 1, "UU" )) return 0;
	MOAITransform* t1=state.GetLuaObject<MOAITransform>(1,true);
	MOAITransform* t2=state.GetLuaObject<MOAITransform>(2,true);
	if( !t1 || !t2 ) return 0;
	ZLVec3D v1=t1->GetLoc();
	ZLVec3D v2=t2->GetLoc();
	float dst = (v1 - v2).Length();
	state.Push(dst);
	return 1;
}

// int MDDHelper::_isBlocked(lua_State *L){
// 	MOAILuaState state (L);
// 	if ( !state.CheckParams ( 1, "U" )) return 0;
// 	MOAIAction *blocked = state.GetLuaObject<MOAIAction>(1,true);
// 	lua_pushboolean(state, blocked->IsBlocked());
// 	return 1;
// }

// int MDDHelper::_getActionStat(lua_State *L){
// 	MOAILuaState state (L);
// 	if ( !state.CheckParams(1,"U") ) return 0;
// 	MOAIAction *action = state.GetLuaObject<MOAIAction>(1,true);
// 	state.Push(action->GetPass());
// 	state.Push(action->GetIsNew());
// 	return 2;
// }

// int MDDHelper::_setActionPass(lua_State *L){
// 	MOAILuaState state (L);
// 	if (!state.CheckParams(1,"UN")) return 0;
// 	MOAIAction *action = state.GetLuaObject<MOAIAction>(1,true);
// 	u32 pass=state.GetValue<u32>(2,0);
// 	action->SetPass(pass);
// 	return 0;
// }

MDDHelper::MDDHelper(){
	RTTI_BEGIN
		RTTI_SINGLE(MOAILuaObject)
	RTTI_END
}

MDDHelper::~MDDHelper(){}

void MDDHelper::RegisterLuaClass(MOAILuaState &state){
	luaL_Reg regTable [] = {
		{ "canSeeCell",		_canSeeCell },
		{ "getSeeableCells",	_getSeeableCells },
		{ "blockAction",	_blockAction },
		{	"floodFillGrid", _fillGrid},
		{	"tileToBits", _tileToBits},
		{	"bitsToTile", _bitsToTile},
		{	"setTileBit", _setTileBit},
		{	"getTileBit", _getTileBit},
		{	"distanceBetweenTransform", _distanceBetweenTransform},

		// { "isBlocked",	_isBlocked },
		// { "getActionStat",	_getActionStat },
		// { "setActionPass",	_setActionPass },
		
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}


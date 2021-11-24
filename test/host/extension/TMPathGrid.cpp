#include "TMPathGrid.h"

void quickFill(ZLLeanArray<u32>& buffer, int w, int h,	//buffer
								int pw, int ph,													//partition
								int fx, int fy, TMPathSection* section, //target
								TMPathSectionList& sections, u32 & seq, ZLLeanArray<u32>& seqs);

//PathGrid

//TODO: serialization, partition split

void TMPathSection::addNeighbor(TMPathSection* section){
	if(hasNeighbor(section)) return;
	assert(section!=this);
	mNeighbors.insert(section);
	section->addNeighbor(this);
	// printf("addNeibor %d -> %d \n",this->mId, section->mId);
}

bool TMPathSection::hasNeighbor(TMPathSection* section){
	return mNeighbors.contains(section);
}

bool TMPathSection::isAlone(){
	return mNeighbors.empty();
}

void TMPathSection::dropAll(){
	STLSet < TMPathSection* >::iterator itr;
	for ( itr = mNeighbors.begin (); itr != mNeighbors.end (); ++itr ) {
		(*itr)->mNeighbors.erase(this);
	}
}

u32 connectCheckSeq=1;
TMPathSection* searchStack[4096];
u32 searchStackTop=0;

bool TMPathSection::checkConnected(TMPathSection* target, u32 passFlags, u32 teamFlags, bool noEnter){
	connectCheckSeq++;
	searchStackTop=0;
	searchStack[searchStackTop++]=this;

	if( !this->checkFlags(passFlags,teamFlags) ) return false;

	if(this==target) return true;

	// if(this==target) return true;
	STLSet < TMPathSection* >::iterator itr;
	
	while(searchStackTop>0){
		TMPathSection* s = searchStack[--searchStackTop];
		for ( itr = s->mNeighbors.begin (); itr != s->mNeighbors.end (); ++itr ) {
			TMPathSection* s1=*itr;
			
			if(s1==target) {
				return noEnter || s1->checkFlags(passFlags, teamFlags);
			}

			if(s1->mSeq!=connectCheckSeq) {
				s1->mSeq=connectCheckSeq;
				if(s1->checkFlags(passFlags, teamFlags)) searchStack[searchStackTop++]=s1;
			}
		}
	}

	return false;
}

bool TMPathSection::isJustChecked(){
	return mSeq==connectCheckSeq;
}


int TMPathGrid::_init(lua_State *L){
	MOAI_LUA_SETUP(TMPathGrid, "UNNNN")

	u32 width           = state.GetValue<u32>(2,0);
	u32 height          = state.GetValue<u32>(3,0);

	float tileWidth     = state.GetValue<float>(4,0);
	float tileHeight    = state.GetValue<float>(5,0);

	u32 partitionWidth  = state.GetValue<u32>(6,0);
	u32 partitionHeight = state.GetValue<u32>(7,0);

	self->init( width,height, tileWidth,tileHeight, partitionWidth,partitionHeight );
	return 0;
}

int TMPathGrid::_registerTileType(lua_State* L){
	MOAI_LUA_SETUP(TMPathGrid, "UNN")
	u32 code=state.GetValue<u32>(2,0);
	u32 passMask=state.GetValue<u32>(3,self->mDefaultPassFlags);
	u32 teamMask=state.GetValue<u32>(4,self->mDefaultTeamFlags);
	self->registerTileType(code,passMask,teamMask);
	return 0;
}

int TMPathGrid::_isReachable(lua_State *L){
	MOAI_LUA_SETUP(TMPathGrid, "UNNNN")
	u32 x0=state.GetValue<u32>(2,1)-1;
	u32 y0=state.GetValue<u32>(3,1)-1;
	u32 x1=state.GetValue<u32>(4,1)-1;
	u32 y1=state.GetValue<u32>(5,1)-1;
	
	u32 passFlags=state.GetValue<u32>(6, self->mDefaultPassFlags);
	u32 teamFlags=state.GetValue<u32>(7, self->mDefaultTeamFlags);
	bool dontEnter=state.GetValue<bool>(8,0);

	state.Push (self->isReachable(x0,y0,x1,y1,passFlags, teamFlags, dontEnter));
	return 1;
}

int TMPathGrid::_isSeeable(lua_State *L){
	MOAI_LUA_SETUP(TMPathGrid, "UNNNN")
	u32 x0=state.GetValue<u32>(2,1)-1;
	u32 y0=state.GetValue<u32>(3,1)-1;
	u32 x1=state.GetValue<u32>(4,1)-1;
	u32 y1=state.GetValue<u32>(5,1)-1;

	u32 passFlags=state.GetValue<u32>(6, self->mDefaultPassFlags);
	u32 teamFlags=state.GetValue<u32>(7, self->mDefaultTeamFlags);

	state.Push (self->isSeeable(x0,y0,x1,y1,passFlags,teamFlags));
	return 1;
}

int TMPathGrid::_isTileBlocked(lua_State *L){
	MOAI_LUA_SETUP(TMPathGrid, "UNN")
	u32 x=state.GetValue<u32>(2,1)-1;
	u32 y=state.GetValue<u32>(3,1)-1;

	u32 passFlags=state.GetValue<u32>(4,self->mDefaultPassFlags);
	u32 teamFlags=state.GetValue<u32>(5,self->mDefaultTeamFlags);
	state.Push(self->isTileBlocked(x,y,passFlags,teamFlags));
	return 1;
}

int TMPathGrid::_getSeeableCells(lua_State *L){
	MOAI_LUA_SETUP(TMPathGrid, "UNNN")
	
	int x=state.GetValue <int> (2, 1)-1;
	int y=state.GetValue <int> (3, 1)-1;

	int range=state.GetValue <int> (4, 3);

	u32 passFlags=state.GetValue <u32> (5, 0);
	u32 teamFlags=state.GetValue <u32> (6, 0);

	int w=self->mWidth, h=self->mHeight;

	int x0,y0,x1,y1;
	x0=x-range; if(x0<0) x0=0;
	y0=y-range; if(y0<0) y0=0;
	x1=x+range; if(x1>=w) x1=w-1;
	y1=y+range; if(y1>=h) y1=h-1;
	int count=0;
	//TODO: optimize this use decent algorithm
	lua_newtable(L);
	for(int xx=x0; xx<=x1; xx++)
		for(int yy=y0; yy<=y1; yy++)
		{
				int dx=xx-x, dy=yy-y;
				if (dx*dx+dy*dy<=range*range && self->isSeeable(x,y,xx,yy,passFlags,teamFlags)){
					count++;
					lua_pushnumber(L, count);
					lua_pushnumber(L, yy*w + xx +1) ;
					lua_settable(L, -3);
				}
		}

	return 1;
}

int TMPathGrid::_getTile(lua_State* L){
	MOAI_LUA_SETUP(TMPathGrid, "UNN")
	u32 x=state.GetValue<u32>(2,1)-1;
	u32 y=state.GetValue<u32>(3,1)-1;
	u32 tile=self->getTile(x,y);
	state.Push(tile);
	return 1;
}

int TMPathGrid::_getSectionId(lua_State* L){
	MOAI_LUA_SETUP(TMPathGrid, "UNN")	
	u32 x=state.GetValue<u32>(2,1)-1;
	u32 y=state.GetValue<u32>(3,1)-1;
	u32 sectionId=self->getSectionId(x,y);
	state.Push(sectionId);
	return 1;
}

int TMPathGrid::_getCodeGrid(lua_State* L){
	MOAI_LUA_SETUP(TMPathGrid, "U")
	self->mCodeGrid->PushLuaUserdata(state);
	return 1;
}

int TMPathGrid::_getSectionGrid(lua_State* L){
	MOAI_LUA_SETUP(TMPathGrid, "U")
	self->mSectionGrid->PushLuaUserdata(state);
	return 1;	
}

int TMPathGrid::_setDefaultPassFlags (lua_State* L){
	MOAI_LUA_SETUP(TMPathGrid, "UN")
	u32 flags=state.GetValue<u32>(2,0xfffffff);
	self->mDefaultPassFlags=flags;	
	return 0;
}

int TMPathGrid::_setDefaultTeamFlags (lua_State* L){
	MOAI_LUA_SETUP(TMPathGrid, "UN")
	u32 flags=state.GetValue<u32>(2,0xfffffff);
	self->mDefaultTeamFlags=flags;	
	return 0;
}

int TMPathGrid::_setTile (lua_State* L){
	MOAI_LUA_SETUP(TMPathGrid, "UNNN")
	u32 x=state.GetValue<u32>(2,1)-1;
	u32 y=state.GetValue<u32>(3,1)-1;
	u32 tile=state.GetValue<u32>(4,0);

	TMPathSection* section=self->setTile(x,y,tile);
	if(section){
		state.Push(section->mId);
		return 1;
	}
	return 0;
}

u32 TMPathGrid::getSectionId(u32 x, u32 y){
	return mSectionGrid->GetTile(x,y);
}

TMPathSection* TMPathGrid::getSection(u32 x, u32 y){
	u32 id=mSectionGrid->GetTile(x,y);
	return mSections.get(id);
}

u32 TMPathGrid::getTile(u32 x, u32 y){
	return mCodeGrid->GetTile(x,y);
	// u32 sectionId=getSectionId(x,y);
	// TMPathSection* section= mSections.get(sectionId);
	// if(section) return section->mCode;
	// return 0;
}

bool TMPathGrid::isTileBlocked(u32 x, u32 y, u32 passFlags, u32 teamFlags){
	u32 id=mSectionGrid->GetTile(x,y);
	if(id==0) return true;
	TMPathSection* s = mSections.get(id);
	return !s->checkFlags(passFlags, teamFlags);
}

bool TMPathGrid::isReachable(int x0,int y0, int x1, int y1, u32 passFlags, u32 teamFlags, bool noEnter){
	TMPathSection* start=getSection(x0,y0);
	TMPathSection* end  =getSection(x1,y1);
	
	if(!start || !end) return false;


	if(noEnter && 
			(end->mCode == 0 || !end->checkFlags(passFlags, teamFlags)) 
		)
	{// trying to reach a empty section, try its neighbor
		connectCheckSeq++	;
		TMPathSection *n=getSection(x1,y1+1);
		TMPathSection *e=getSection(x1+1,y1);
		TMPathSection *s=getSection(x1,y1-1);		
		TMPathSection *w=getSection(x1-1,y1);		
		if( n->mCode!=0 && n->checkConnected(start,passFlags, teamFlags, noEnter) ) return true;
		if( e->mCode!=0 && !e->isJustChecked() && e->checkConnected(start,passFlags, teamFlags, noEnter)	) return true;
		if( s->mCode!=0 && !s->isJustChecked() && s->checkConnected(start,passFlags, teamFlags, noEnter)	) return true;
		if( w->mCode!=0 && !w->isJustChecked() && w->checkConnected(start,passFlags, teamFlags, noEnter)	) return true;
	}else{
		if(start->mCode==0 || end->mCode==0) return false;
		return start->checkConnected(end,passFlags,teamFlags, noEnter);
	}

	return false;
}

bool TMPathGrid::isSeeablePoint( float x0, float y0, float x1, float y1, u32 passFlags, u32 teamFlags ) {
	float dx = x1 - x0;
	float dy = y1 - y0;
	//x-axis
	if( dx != 0 ) {
		int tx = (int) x0 / mTileWidth;
		float r = dy / dx;

		if( dx > 0 ) {
			tx += 1;
			float off = tx * mTileWidth - x0;
			while( off < dx ) {	
				float y = y0 + off * r;
				int ty = (int) ( y / mTileHeight );				
				if( isTileBlocked( tx, ty, passFlags, teamFlags ) ) return false;
				if( (float) ty * mTileHeight == y ) { //corner
					if( isTileBlocked( tx - 1, ty, passFlags, teamFlags ) ) return false;
				}
				off += mTileWidth;
				tx += 1;
			}
		} else { //dx < 0
			float off = tx * mTileWidth - x0;
			while( off > dx ) {	
				float y = y0 + off * r;
				int ty = (int) ( y / mTileHeight );
				if( isTileBlocked( tx - 1, ty, passFlags, teamFlags ) ) return false;
				if( (float) ty * mTileHeight == y ) { //corner
					if( isTileBlocked( tx, ty, passFlags, teamFlags ) ) return false;
				}
				off -= mTileWidth;
				tx -= 1;
			}
		}
		
	}

	if( dy != 0 ) {
		int ty = (int) y0 / mTileHeight;
		float r = dx / dy;

		if( dy > 0 ) {
			ty += 1;
			float off = ty * mTileHeight - y0;
			while( off < dy ) {	
				float x = x0 + off * r;
				int tx = (int) ( x / mTileWidth );
				if( (float) tx * mTileWidth == x ) { //corner
					if( isTileBlocked( tx, ty - 1, passFlags, teamFlags ) ) return false;
				} else {
					if( isTileBlocked( tx, ty, passFlags, teamFlags ) ) return false;
				}
				off += mTileHeight;
				ty += 1;
			}
		} else { //dy < 0
			float off = ty * mTileHeight - y0;
			while( off > dy ) {	
				float x = x0 + off * r;
				int tx = (int) ( x / mTileWidth );
				if( (float) tx * mTileWidth == x ) { //corner
					if( isTileBlocked( tx, ty, passFlags, teamFlags ) ) return false;
				} else {
					if( isTileBlocked( tx, ty - 1, passFlags, teamFlags ) ) return false;
				}
				off -= mTileHeight;
				ty -= 1;
			}
		}
	}

	return true;
}

bool TMPathGrid::isSeeable( u32 x0, u32 y0, u32 x1, u32 y1, u32 passFlags, u32 teamFlags){
	int dx = x1 - x0;
	int dy = y1 - y0;

	if( dx==0 && dy==0 ) return true;

	if( dx*dx > dy*dy ){ //move along x axis
		float r = (float)dy/(float)dx;
		int step = dx>0 ? 1: -1;
		int ddx = step;
		int bx = x0;
		int by = y0;

		while( true ){
			int x = x0 + ddx;
			int y = y0 + ((float)ddx * r + 0.5f);
			if( by != y ){ //avoid diagonal cross
				if( isTileBlocked( bx, y, passFlags, teamFlags) 
					&& isTileBlocked( x, by, passFlags, teamFlags) ) 
					return false;
			}
			if( isTileBlocked(x,y,passFlags, teamFlags) ) return false;
			if( ddx == dx ) break ;
			ddx += step;
			by = y;
			bx = x;
		}

	}else{ //move along y axis
		float r = (float)dx/(float)dy;
		int step = dy>0 ? 1: -1;
		int ddy = step;
		int bx = x0;
		int by = y0;

		while( true ){
			int y = y0 + ddy;
			int x = x0 + ((float)ddy * r + 0.5f);
			if( bx != x ){ //avoid diagonal cross
				if( isTileBlocked( bx, y, passFlags, teamFlags) 
					&& isTileBlocked( x, by, passFlags, teamFlags) )
					return false;
			}
			if( isTileBlocked(x,y,passFlags, teamFlags) ) return false;
			if ( ddy == dy ) break;
			ddy += step;
			bx = x;
			by = y;
		}

	}	
	return true;
}


TMPathSection* TMPathGrid::setTile(u32 x, u32 y, u32 code){
	
	//find connected section
	TMPathSection* c0=getSection(x,y);
	u32 code0=c0->mCode;
	if(code0==code) return c0;

	TMPathSection* c=0;

	TMPathSection* n=getSection(x,y+1);	
	TMPathSection* e=getSection(x+1,y);	
	TMPathSection* s=getSection(x,y-1);	
	TMPathSection* w=getSection(x-1,y);

	TMPathSection* ne=getSection(x+1,y+1);	
	TMPathSection* se=getSection(x+1,y-1);	
	TMPathSection* sw=getSection(x-1,y-1);	
	TMPathSection* nw=getSection(x-1,y+1);

	u32 nc=n->mCode;
	u32 wc=w->mCode;
	u32 ec=e->mCode;
	u32 sc=s->mCode;

	if     (code== 0){c=mEmptySection;}
	else if(code==nc){c=n;}
	else if(code==ec){c=e;}
	else if(code==sc){c=s;}
	else if(code==wc){c=w;}
	else{	c=allocateSection(code);}
	
	mSectionGrid->SetTile(x,y,c->mId);
	mCodeGrid->SetTile(x,y,code);
	
	if(code0!=0 && code0!=nc && code0!=ec && code0!=sc && code0!=wc){		
		removeSection(c0);
	}

	if(code!=0){
		if(nc!=0 && code!=nc){c->addNeighbor(n);}
		if(ec!=0 && code!=ec){c->addNeighbor(e);}
		if(sc!=0 && code!=sc){c->addNeighbor(s);}
		if(wc!=0 && code!=wc){c->addNeighbor(w);}
	}

	//Connectivity: N->E->S->W->N	
	int block=0;
	int n_e,e_s,s_w,w_n;
	if(nc==0 || ec==0 || ne->mCode==0 ) {n_e=10;} else {n_e=(n!=ne)+(e!=ne);}
	if(ec==0 || sc==0 || se->mCode==0 ) {e_s=10;} else {e_s=(e!=se)+(s!=se);}
	if(sc==0 || wc==0 || sw->mCode==0 ) {s_w=10;} else {s_w=(s!=sw)+(w!=sw);}
	if(wc==0 || nc==0 || nw->mCode==0 ) {w_n=10;} else {w_n=(w!=nw)+(n!=nw);}

	int i_n=0,i_e=0,i_w=0,i_s=0;

	if(nc!=0){
		if(nc==code && n!=c){i_n=1;}
		else if(nc==code0 && 
			(  ((ec>0)&&(n_e>1 && e_s+s_w+w_n >1)) 
			|| ((sc>0)&&(n_e+e_s>1 && s_w+w_n >1)) 
			|| ((wc>0)&&(w_n>1 && e_s+s_w+n_e >1))
			)
		) {i_n=2;}
	}

	if(ec!=0){
		if(ec==code && e!=c){i_e=1;}
		else if(ec==code0 && 
			(  ((sc>0)&&(e_s>1 && s_w+w_n+n_e >1)) 
			|| ((wc>0)&&(e_s+s_w>1 && w_n+n_e >1)) 
			|| ((nc>0)&&(n_e>1 && e_s+s_w+w_n >1))
			)
		) {i_e=2;}
	}
	
	if(sc!=0){
		if(sc==code && s!=c){i_s=1;}
		else if(sc==code0 && 
			(  ((wc>0)&&(s_w>1 && w_n+n_e+e_s >1)) 
			|| ((nc>0)&&(s_w+w_n>1 && n_e+e_s >1)) 
			|| ((ec>0)&&(e_s>1 && s_w+w_n+n_e >1))
			)
		) {i_s=2;}
	}
	
	if(wc!=0){
		if(wc==code && w!=c){i_w=1;}
		else if(wc==code0 && 
			(  ((nc>0)&&(w_n>1 && n_e+e_s+s_w >1)) 
			|| ((ec>0)&&(w_n+n_e>1 && e_s+s_w >1)) 
			|| ((sc>0)&&(s_w>1 && w_n+n_e+e_s >1))
			)
		) {i_w=2;}
	}
	// printf("op:%d ,%d ,%d ,%d \n", i_n,i_e,i_s,i_w);
	#define QUICKFILL(x,y,section) quickFill(tiles,mWidth,mHeight,\
														mPartitionWidth,mPartitionHeight, x , y , section,\
														mSections, mNeighborSeq, mSectionSeqs);
	#define NOTCHANGED(x,y,id) mSectionGrid->GetTile(x,y) == id

	ZLLeanArray <u32> & tiles=mSectionGrid->GetTileArray();

	u32 eid=e->mId, sid=s->mId, wid=w->mId;

	bool blockedRemoved=false;
	//process blocked tile first
	if(i_n==2){//block
		removeSection(n); blockedRemoved=true;
		QUICKFILL(x,y+1,allocateSection(nc));
	}
	if(i_e==2 && NOTCHANGED(x+1,y,eid)){//block
		if(!blockedRemoved){removeSection(e); blockedRemoved=true;}
		QUICKFILL(x+1,y,allocateSection(ec));
	}
	if(i_s==2 && NOTCHANGED(x,y-1,sid)){//block
		if(!blockedRemoved){removeSection(s); blockedRemoved=true;}
		QUICKFILL(x,y-1,allocateSection(sc));
	}
	if(i_w==2 && NOTCHANGED(x-1,y,wid)){//block
		if(!blockedRemoved){removeSection(w); blockedRemoved=true;}
		QUICKFILL(x-1,y,allocateSection(wc));
	}

	//then connected tiles
	if(i_n==1){//unblock		
		QUICKFILL(x,y+1,c);
	}

	if(i_e==1 && NOTCHANGED(x+1,y,eid)){//unblock
		removeSection(e);
		QUICKFILL(x+1,y,c);
	}

	if(i_s==1 && NOTCHANGED(x,y-1,sid)){//unblock
		removeSection(s);
		QUICKFILL(x,y-1,c);
	}

	if(i_w==1 && NOTCHANGED(x-1,y,wid)){//unblock
		removeSection(w);
		QUICKFILL(x-1,y,c);
	}

	return c;
}


TMPathSection* TMPathGrid::allocateSection(u32 code){
	if(code==0){return mEmptySection;}
	TMPathSection* s=new TMPathSection();
	s->mCode=code;
	s->mSeq=0;
	TMPathGridTileType* tt= mTileTypes[code];
	if(tt!=0) {
		s->mPassMask=tt->mPassMask;
		s->mTeamMask=tt->mTeamMask;
	}else{
		s->mPassMask=0;
		s->mTeamMask=0xffff;
	} 
	mSections.insert(s);
	return s;
}

TMPathSection* TMPathGrid::reallocateSection(TMPathSection* section){
	section->dropAll();
	mSections.remove(section->mId);
	mSections.insert(section);
	return section;
}

void TMPathGrid::removeSection(TMPathSection* section){
	section->dropAll();
	mSections.remove(section->mId);
	delete section;
}


//================================================================//
// TMPathGrid
//================================================================//

//----------------------------------------------------------------//
float TMPathGrid::ComputeHeuristic ( PathGraphParam& params, const MOAICellCoord& c0, const MOAICellCoord& c1 ) {

	float hMove = ( float )abs ( c1.mX - c0.mX );
	float vMove = ( float )abs ( c1.mY - c0.mY );
	return ABS ( hMove * params.mHCost ) + ABS ( vMove * params.mVCost );
}

//----------------------------------------------------------------//
void TMPathGrid::PushNeighbor ( MOAIPathFinder& pathFinder, PathGraphParam& params, u32 tile0, int xTile, int yTile, float moveCost ) {

	MOAICellCoord coord = this->mCodeGrid->GetCellCoord ( xTile, yTile );

	if ( this->mCodeGrid->IsValidCoord ( coord )) {
		
		u32 clearance = this->ComputeClearance( pathFinder, xTile, yTile );

		if ( clearance >= 2 ) {
		// if ( pathFinder.CheckMask ( tile1 ) ) {
			u32 tile1 = this->mCodeGrid->GetTile ( xTile, yTile );
			
			int neighborID = this->mCodeGrid->GetCellAddr ( coord );
			
			if ( !pathFinder.IsVisited ( neighborID )) {
				
				float g = ( moveCost + pathFinder.ComputeTerrainCost ( moveCost, tile0, tile1 )) * params.mGWeight;
				
				int targetID = pathFinder.GetTargetNodeID ();
				MOAICellCoord targetCoord = this->mCodeGrid->GetCellCoord ( targetID );
				
				float h = this->ComputeHeuristic ( params, coord, targetCoord ) * params.mHWeight;
				
				pathFinder.PushState ( neighborID, g, h );
			}
		}
	}
}

u32 TMPathGrid::ComputeClearance( MOAIPathFinder& pathFinder, int xTile, int yTile ) {
	u32 clearance = 0;
	u32 finderSize = 2;
	int x1, y1, dx, dy, tile;

	for( u32 i = 0; i < finderSize; ++i ) {
		x1 = xTile + i;
		y1 = yTile + i;
		MOAICellCoord coord = this->mCodeGrid->GetCellCoord ( x1, y1 );
		if ( !this->mCodeGrid->IsValidCoord ( coord )) return clearance;

		for( dx = 0; dx <= i; dx++ ) {
			tile = this->mCodeGrid->GetTile ( xTile + dx, y1 );
			if( !pathFinder.CheckMask ( tile ) ) return clearance;
		}

		for( dy = 1; dy <= i; dy++ ) {
			tile = this->mCodeGrid->GetTile ( x1, yTile + dy );
			if( !pathFinder.CheckMask ( tile ) ) return clearance;
		}

		clearance++;
	}
	// printf( "clearance:%d\n", clearance );
	return clearance;
}

//----------------------------------------------------------------//
void TMPathGrid::PushNeighbors ( MOAIPathFinder& pathFinder, int nodeID ) {
	
	if ( !this->mCodeGrid ) return;
	
	PathGraphParam params;
	
	params.mGWeight = pathFinder.GetGWeight ();
	params.mHWeight = pathFinder.GetHWeight ();
	
	params.mHeuristic = pathFinder.GetHeuristic ();
	
	u32 flags = pathFinder.GetFlags ();
	
	MOAICellCoord coord = this->mCodeGrid->GetCellCoord ( nodeID );
	
	int xTile = coord.mX;
	int yTile = coord.mY;
	
	u32 tile0 = this->mCodeGrid->GetTile ( xTile, yTile );
	
	switch ( this->mCodeGrid->GetShape ()) {
	
		case MOAIGridSpace::RECT_SHAPE: {
			
			params.mHCost = this->mCodeGrid->GetCellWidth ();
			params.mVCost = this->mCodeGrid->GetCellHeight ();
			params.mDCost = sqrtf (( params.mHCost * params.mHCost ) + ( params.mVCost * params.mVCost ));
			params.mZCost = 0.0f;
			
			this->PushNeighbor ( pathFinder, params, tile0, xTile - 1, yTile, params.mHCost );
			this->PushNeighbor ( pathFinder, params, tile0, xTile + 1, yTile, params.mHCost );
			this->PushNeighbor ( pathFinder, params, tile0, xTile, yTile + 1, params.mVCost );
			this->PushNeighbor ( pathFinder, params, tile0, xTile, yTile - 1, params.mVCost );
			break;
		}
	}
}

void TMPathGrid::init(u32 width, u32 height, float tileWidth, float tileHeight, u32 partitionWidth, u32 partitionHeight){
	
	mWidth      = width;
	mHeight     = height;
	mTileWidth  = tileWidth;
	mTileHeight = tileHeight;
	mPartitionWidth  = partitionWidth;
	mPartitionHeight = partitionHeight;

	mSectionGrid->Init( width, height, tileWidth, tileHeight );
	mSectionGrid->GetTileArray().Init(mSectionGrid->GetTotalCells());
	mSectionGrid->Fill(0);

	mCodeGrid->Init( width, height, tileWidth, tileHeight );
	mCodeGrid->GetTileArray().Init(mCodeGrid->GetTotalCells());
	mCodeGrid->Fill(0);
}

void TMPathGrid::registerTileType(u32 code, u32 passMask, u32 teamMask){
	TMPathGridTileType* tileType=new TMPathGridTileType;
	tileType->mPassMask=passMask;
	tileType->mTeamMask=teamMask;
	tileType->mCode=code;
	mTileTypes[code]=tileType;
}

TMPathGrid::TMPathGrid():
	mWidth(0),
	mHeight(0),
	mPartitionWidth(0),
	mPartitionHeight(0),
	mMaxSection(0),
	mNeighborSeq(0),
	mDefaultPassFlags(0xffffffff),
	mDefaultTeamFlags(0xffffffff),
	mSections(MAX_SECTION_COUNT)	
{
	RTTI_BEGIN
		RTTI_EXTEND(MOAIPathGraph)
	RTTI_END

	mSectionGrid.Set ( *this, new MOAIGrid ());
	mCodeGrid.Set ( *this, new MOAIGrid ());

	mEmptySection = new TMPathSection();
	mSections.insert(mEmptySection);
	
	mSectionSeqs.Init(MAX_SECTION_COUNT);
	mSectionSeqs.Fill(0);
}

TMPathGrid::~TMPathGrid()
{
	mSections.clear();
	for (STLMap<u32,TMPathGridTileType*>::iterator it=mTileTypes.begin(); it!=mTileTypes.end(); ++it){
		TMPathGridTileType *tt=it->second;
		delete tt;
	}
	mSectionGrid.Set(*this, 0);
	mCodeGrid.Set(*this, 0);
}

void TMPathGrid::RegisterLuaClass(MOAILuaState &state){	
	UNUSED(state);
}

void TMPathGrid::RegisterLuaFuncs(MOAILuaState &state){

	luaL_Reg regTable [] = {
		{ "setTile",					_setTile },
		{ "getTile",					_getTile },
		{ "setDefaultPassFlags",					_setDefaultPassFlags },
		{ "setDefaultTeamFlags",					_setDefaultTeamFlags },
		{ "getSectionId",			_getSectionId },
		{ "getCodeGrid",			_getCodeGrid },
		{ "getSectionGrid",			_getSectionGrid },

		{ "isReachable",			_isReachable },
		{	"getSeeableCells",	_getSeeableCells},
		{ "isSeeable",				_isSeeable },
		{ "isTileBlocked",		_isTileBlocked },

		{ "init",							_init },
		{ "registerTileType",	_registerTileType },
		
		// { "getTile",				_getTile },

		{ NULL, NULL }
	};	
	luaL_register ( state, 0, regTable );	
}




////////



#define FILL_QUEUE_SIZE (5000 * 4)

u32 fillQueue[FILL_QUEUE_SIZE];
u32 fillHead=0, fillTail=0;
inline void pushLine(int x0, int x1, int y, int dir){
	fillQueue[fillTail]=x0;
	fillQueue[fillTail+1]=x1;
	fillQueue[fillTail+2]=y;
	fillQueue[fillTail+3]=dir;

	fillTail=(fillTail+4) % FILL_QUEUE_SIZE;
}

inline bool popLine(int &x0, int& x1, int& y, int& dir){
	if(fillHead >= fillTail) return false;
	x0=fillQueue[fillHead];
	x1=fillQueue[fillHead+1];
	y=fillQueue[fillHead+2];
	dir=fillQueue[fillHead+3];
	fillHead=(fillHead+4) % FILL_QUEUE_SIZE;
	return true;
}

inline void resetFillQueue(){
	fillHead=0;fillTail=0;
}

inline bool checkTileAndNeighbor(u32 code, u32 old, u32 newCode,
								TMPathSection* section, //target
								TMPathSectionList& sections, u32 seq, ZLLeanArray<u32>& seqs){
	if(code==old) return true;
	if(code==0 || code==newCode) return false;
	if(seqs[code]<seq){
		TMPathSection* s=sections.get(code);
		seqs[code]=seq;
		section->addNeighbor(s);
	}
	return false;
}

// inline getTile(ZLLeanArray<u32> &buf, fx,fy)
#define GETTILE(x,y) ( (y>=0 && y<h && x>=0 && x<w) ? buffer[(y)*w+(x)] : 0)
#define SETTILE(x,y,v) buffer[(y)*w+(x)] = v
#define FILLABLE(x,y) checkTileAndNeighbor(GETTILE(x,y),old,code,section,sections,seq,seqs)

//Quick Fill
void quickFill(ZLLeanArray<u32>& buffer, int w, int h,	//buffer
								int pw, int ph,													//partition
								int fx, int fy, TMPathSection* section, //target
								TMPathSectionList& sections, u32 & seq, ZLLeanArray<u32>& seqs){ 			//for avoid repeative checking
	//TODO: partition window 

	u32 old=GETTILE(fx,fy);
	u32 code=section->mId;

	if(old==code) return ;

	//determine partition
	int col,row;
	int px0,py0,px1,py1;
	px0=0;py0=0;px1=w;py1=h;
	
	// col=fx/pw;
	// row=fy/ph;

	// px0=col*pw; px1=px0+pw; if(px1>w) px1=w;
	// py0=row*ph; py1=py0+ph; if(py1>h) py1=h;
	// printf("fill:%d,%d,%d -> %d\n",fx,fy,px0,px1);

	seq++;

	resetFillQueue();
	pushLine(fx,fx,fy,-1);	
	if(fy<h-1 && FILLABLE(fx,fy+1)) pushLine(fx,fx,fy+1,1);

	int l,r,y,d; //left, right, y,  direction
	while(popLine(l,r,y,d)){
		int nl=-1;
		int nr=-1;

		//span1: < left         : check neighbor tile
		if(GETTILE(l,y)==old){
			for(int x=l-1;x>=px0;x--){				
				if(FILLABLE(x,y)){
					SETTILE(x,y, code);
					nl=x;

					//check opposite					
					if(FILLABLE(x,y-d) && nr<0){ 
						nr=x;
					}else if(nr>=0){
						pushLine(x,nr,y-d,-d); //push oppopsite
						nr=-1;
					}

				}else{
					if(nr>=0){
						pushLine(x,nr,y-d,-d);
						nr=-1;
					}
					break;
				}
			}
		}
		//reach edge
		if(nr>=0){
			pushLine(0,nr,y-d,-d);
			nr=-1;
		}

		//span2: left<= =>right : no check for neighbor tile
		for(int x=l;x<=r;x++){			
			if(FILLABLE(x,y)){
				SETTILE(x,y, code); if(nl<0) nl=x;
			}else if(nl>=0){
				pushLine(nl, x-1, y + d, d);
				nl=-1;
			}
		}
		if(nl<0) continue;

		//span3: right >        : check neighbor tile
		int nl1=-1;
		for(int x=r+1; x<px1; x++){
			if(FILLABLE(x,y)){
				SETTILE(x,y, code); if(nl<0) nl=x;
				//check opposite				
				if(FILLABLE(x,y-d)){
					if(nl1<0) nl1=x;
				}else if(nl1>=0){
					pushLine(nl1, x-1, y-d, -d);
					nl1=-1;
				}
			}else{
				if(nl>=0){	pushLine(nl, x-1, y+d, d);	nl=-1;}
				if(nl1>=0){ pushLine(nl1, x-1, y-d, -d);	nl1=-1;}
				break;
			}
		}

		//reach edge
		if(nl>=0){	pushLine(nl,w-1, y+d, d);	nl=-1;}
		if(nl1>=0){ pushLine(nl1, w-1, y-d, -d);	nl1=-1;}

	}
}
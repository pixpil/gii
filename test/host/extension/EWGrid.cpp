#include "EWGrid.h"


EWGrid::EWGrid () {
	RTTI_BEGIN
		RTTI_EXTEND ( MOAIGrid )
	RTTI_END
}

EWGrid::~EWGrid () {
}



//----------------------------------------------------------------//
void EWGrid::Draw ( MOAIDeck *deck, MOAIDeckRemapper *remapper, const MOAICellCoord &c0, const MOAICellCoord &c1 ) {
	float tileWidth = this->GetTileWidth ();
	float tileHeight = this->GetTileHeight ();
	deck->PreGridDraw();
	for ( int y = c1.mY; y > c0.mY; --y ) {
		for ( int x = c0.mX; x <= c1.mX; ++x ) {
			
			MOAICellCoord wrap = this->WrapCellCoord ( x, y );
			u32 idx = this->GetTile ( wrap.mX, wrap.mY );
			
			MOAICellCoord coord ( x, y );
			ZLVec2D loc = this->GetTilePoint ( coord, MOAIGridSpace::TILE_CENTER );

			deck->Draw ( MOAIDeckRemapper::Remap ( remapper, idx ), loc.mX, loc.mY, -loc.mY, tileWidth, tileHeight, 1.0f );
		}
	}
	deck->PostGridDraw();
}


void EWGrid::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIGrid::RegisterLuaClass ( state );
}

void EWGrid::RegisterLuaFuncs	( MOAILuaState& state ) {
	MOAIGrid::RegisterLuaFuncs ( state );
}


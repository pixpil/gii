module 'mock_edit'

addColor( 'white', 1,1,1,1 )
addColor( 'grey', 0.5,0.5,0.5,1 )
addColor( 'black', 0,0,0,1 )
addColor( 'red', 1,0,0,1 )
addColor( 'orange', 1,0.5,0,1 )
addColor( 'yellow', 1,1,0,1 )
addColor( 'green', 0,1,0,1 )
addColor( 'blue', 0,0,1,1 )
addColor( 'purple', 0.5,0,1,1 )
addColor( 'magenta', 1,0,1,1 )
addColor( 'blueGreen', 0,1,1,1 )
addColor( 'yellowGreen', 0.5,1,0,1 )

local alpha = 0.6
local alphaHandle = 0.7

addColor( 'context-bound', hexcolor( '#12ff00', 0.1 ) )

addColor( 'selection', hexcolor( '#62ffef', 0.5 ) )
addColor( 'selection-child', hexcolor( '#24507A', 0.5 ) )
addColor( 'handle-x',  hexcolor( '#f82500', alphaHandle ) )
addColor( 'handle-y',  hexcolor( '#8fc800', alphaHandle ) )
addColor( 'handle-z',  hexcolor( '#4c6bff', alphaHandle ) )
addColor( 'handle-all',hexcolor( '#85edff', alphaHandle ) )
addColor( 'handle-active', hexcolor( '#fffa76', alphaHandle ) )

addColor( 'handle-previous', 1,0,0, .3 )

addColor( 'gizmo_trigger', hexcolor( '#6695ff', 0.1 ) )
addColor( 'gizmo_trigger_border', hexcolor( '#6695ff', 0.7 ) )
addColor( 'gizmo_trigger_target', hexcolor( '#8eff00', 0.7 ) )

addColor( 'cp',           hexcolor( '#1c57ff', alpha ) )
addColor( 'cp:selected',  hexcolor( '#efff00', alpha ) )
addColor( 'cp-border', hexcolor( '#ffffff', alpha ) )

addColor( 'vert',           hexcolor( '#ffbf07', 0.8 ) )


addColor( 'misc',  hexcolor( '#6695ff', 0.1 ) )
addColor( 'misc-transform',  hexcolor( '#b8ff00', 1 ) )

addColor( 'camera-bound', hexcolor( '#ffc900', alpha ) )
addColor( 'camera-guide', hexcolor( '#FF2D0A', alpha * 0.7 ) )

addColor( 'shape-line',  hexcolor( '#ffb1fe', 0.5 ))
addColor( 'shape-fill',  hexcolor( '#ff6cf9', .3 ))

addColor( 'deckcanvas-bound', hexcolor( '#e817ff', alpha ) )
addColor( 'deckcanvas-item', hexcolor( '#36fff6', alpha ) )

addColor( 'range-min', hexcolor( '#684803', alpha ) )
addColor( 'range-max', hexcolor( '#fff451', alpha ) )

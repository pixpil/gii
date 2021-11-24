require 'mock'
function addLayer()
	local l = mock.game:addLayer( 'layer' )
	return l
end

function setLayerName( l, name )
	l:setName( name )
end

function updatePriority()
	for i, l in ipairs( mock.game.layers ) do
		if l.name ~='_GII_EDITOR_LAYER' then
			l.priority = i
		end
	end
	emitSignal( 'layer.update', 'all', 'priority' )
	gii.emitPythonSignal( 'scene.update' )
end

function moveLayerUp( l )
	local layers = mock.game.layers
	local i = table.index( layers, l )
	assert ( i )
	if i >= #layers then return end
	if layers[ i + 1 ].name =='_GII_EDITOR_LAYER' then return end
	table.remove( layers, i )
	table.insert( layers, i + 1 , l )	
	updatePriority()
end

function moveLayerDown( l )
	local layers = mock.game.layers
	local i = table.index( layers, l )
	assert ( i )
	if i <= 1 then return end
	if layers[ i - 1 ].name =='_GII_EDITOR_LAYER' then return end
	table.remove( layers, i )
	table.insert( layers, i - 1 , l )		
	updatePriority()
end

function removeLayer( l )
	mock.game:removeLayer( l )
end


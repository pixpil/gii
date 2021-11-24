function fillSingleTexture( texture, pixmapPath, w,h, ow,oh )
	texture.pixmapPath = pixmapPath
	texture.w = w
	texture.h = h
	texture.ow = ow or w
	texture.oh = oh or h
	texture.u0 = 0
	texture.v0 = 1
	texture.u1 = 1
	texture.v1 = 0
end

-- local function fillPrebuiltAtlasInGroup( tex )
-- end

function fillAtlasTextureGroup( group, atlasCachePath, repackPrebuiltAtlas )
	group.atlasCachePath = atlasCachePath
	local atlasInfoPath = atlasCachePath .. '/atlas.json'
	--reload texture parameters
	local f = io.open( atlasInfoPath, 'r' )
	if not f then 
		error( 'file not found:' .. atlasInfoPath, 2 )   --TODO: proper exception handle
		return nil
	end
	local text = f:read( '*a' )
	f:close()
	local atlasData = MOAIJsonParser.decode( text )
	local prebuiltAtlases = {}
	local atlases = atlasData[ 'atlases' ]
	for i, item in pairs( atlasData[ 'items' ] ) do
		local name  = item.name
		local index = item.index
		local x, y, w, h = unpack( item.rect )

		--FIXME: use real original size
		local ow, oh = w, h
		
		local atlas = atlases[ item.atlas + 1 ]
		local tw, th = unpack( atlas.size )
		local tex = group:findTexture( name )
		if tex:isPrebuiltAtlas() then
			if not repackPrebuiltAtlas then
				local atlasPath = tex.prebuiltAtlasPath
				local atlas = prebuiltAtlases[ atlasPath ]
				if not atlas then
					atlas = mock.PrebuiltAtlas()
					atlas:load( atlasPath )
					prebuiltAtlases[ atlasPath ] = atlas				
				end
				local page  = atlas.pages[ index ]			
				page:updateTexture( item.atlas + 1, x, y, tw, th )
			else
				local atlasPath = tex.prebuiltAtlasPath
				local atlas = prebuiltAtlases[ atlasPath ]
				if not atlas then
					atlas = mock.PrebuiltAtlas()
					prebuiltAtlases[ atlasPath ] = atlas
					local atlas0 = mock.PrebuiltAtlas()
					atlas0:load( atlasPath )
					atlas.originalItems = atlas0:buildItemLookupDict()
				end				
				local page = atlas:getPage( item.atlas + 1 )
				if not page then
					page = atlas:affirmPage( item.atlas + 1 )
					page:updateTexture( item.atlas + 1, 0, 0, tw, th )
				end
				local newItem = page:addItem()
				newItem.name = item.subId
				local oldItem = atlas.originalItems[ item.subId ]
				if oldItem.rotated then
					newItem.w,  newItem.h  = h, w
				else
					newItem.w,  newItem.h  = w, h
				end
				newItem.x,  newItem.y  = x, y  
				newItem.ow, newItem.oh = oldItem.ow, oldItem.oh 
				newItem.ox, newItem.oy = oldItem.ox, oldItem.oy 
				newItem.rotated = oldItem.rotated
			end
		else
			--todo:  crop & rotated
			local u0, v0, u1, v1 = x/tw, y/th, (x+w)/tw, (y+h)/th
			tex.u0 = u0
			tex.v0 = v1
			tex.u1 = u1
			tex.v1 = v0
			tex.x  = x
			tex.y  = y
			tex.w  = w
			tex.h  = h
			tex.ow = ow
			tex.oh = oh
			tex.atlasId = item.atlas + 1 
		end
	end

	for path, atlas in pairs( prebuiltAtlases ) do
		atlas:save( path )
	end
end

function releaseTexPack( path )
	mock.releaseTexPack( path )
end

function loadPrebuiltAtlas( path )
	local atlas = mock.PrebuiltAtlas()
	atlas:load( path )
	return atlas
end

function explodePrebuiltAtlas( base, outputDir )
	
end
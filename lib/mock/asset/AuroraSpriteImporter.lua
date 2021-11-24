lpeg = require'lpeg'

local L=lpeg

local p,s,r,b,lpegv =L.P,L.S,L.R,L.B,L.V
local c,carg,cb,cc,cp,cs,ct,cg,cmt,cf= L.C,L.Carg,L.Cb,L.Cc,L.Cp,L.Cs,L.Ct,L.Cg,L.Cmt,L.Cf

local v=setmetatable({},{__index=function(t,k) return lpegv(k) end})


	local function cnot(patt,f) return cg(cp(),'p0')*(patt+(cb'p0'*cp()/f)) end

	local function cerr(patt,msg) return cnot(patt,function(s0,s1) 
		return error(msg,s1) 
	end) end

	local function c1 (s, o) return s end

	local function t0(tag)	return function() return {tag=tag} end end

	local function t1(tag,a)
		return function(v) return {tag=tag,[a]=v} end
	end

	local function t2(tag,k1,k2)
		--assert(k1 and k2)
		return function(v1,v2) return {tag=tag,[k1]=v1,[k2]=v2} end
	end

	local function t3(tag,k1,k2,k3)
		assert(k1 and k2 and k3)
		return function(v1,v2,v3) return {tag=tag,[k1]=v1,[k2]=v2,[k3]=v3} end
	end

	local function t4(tag,k1,k2,k3,k4)
		assert(k1 and k2 and k3 and k4)
		return function(v1,v2,v3,v4) return {tag=tag,[k1]=v1,[k2]=v2,[k3]=v3,[k4]=v4} end
	end

	local function t5(tag,k1,k2,k3,k4,k5)
		assert(k1 and k2 and k3 and k4 and k5)
		return function(v1,v2,v3,v4,v5) return {tag=tag,[k1]=v1,[k2]=v2,[k3]=v3,[k4]=v4,[k5]=v5} end
	end

	local function tt(tag,t)
		return function(...)  return {tag=tag,[t]={...}} end
	end

	local function tset(field)
		return function(table, value) table[field]=value return table end
	end

	local function tc(tag,c)
		c.tag=tag
		return function() return c end
	end

	 --------------TERMINAL

	local DIGIT=r'09'
	local _=s' \t'^0

	local ALPHA=r'AZ'+r'az'+'_'
	local ALPHADIGIT=ALPHA+DIGIT
	local Name=ALPHA*ALPHADIGIT^0


	local EOL= (p'\n'+p'\r\n'+p'\r')


	-- local LESSEQ=p'<='
	-- local NOTEQ=p'~='
	-- local LESS=p'<'
	-- local GREATEQ=p'>='
	-- local GREATER=p'>'
	-- local EQ=p'=='
	-- local NOTEQ1=p'<>'

	local ASSIGN=p'='
	
		-- local ASSADD=p'+='
	-- local ASSSUB=p'-='
	-- local ASSMUL=p'*='
	-- local ASSDIV=p'/='
	-- local ASSPOW=p'^='
	-- local ASSMOD=p'%='
	-- local ASSCON=p'..='
	-- local ASSAND=p'or='
	-- local ASSOR=p'and='

	-- local ARROWE=p'=>'
	-- local ARROW=p'->'
	-- local STICK=p'|'

	local POPEN,PCLOSE=p'(',p')'
	local BOPEN,BCLOSE=p'{',p'}'
	local SOPEN,SCLOSE=p'[',p']'

	local SLASH=p'/'
	local STAR=p'*'
	local MINUS=p'-'
	local PLUS=p'+'
	local POW=p'^'

	local COMMA=p','
	local COLON=p':'
	local DOT=p'.'
	local DOLLAR=p'$'
	local NUM=p'#'
	local QUES=p'?'
	local AT=p'@'
	local PERCENT=p'%'

	local DOTDOT=p'..'
	local DOTDOTDOT=p'...'
	local DOUBLECOLON=p'::'
	local SEMI=p';'
	
	local QUOTE=p'"'
	local QUOTES=p"'"

	local StringS= QUOTES * c( (p"\\'"+(1-QUOTES-EOL))^0 )* cerr(QUOTES, "broken string")
	local StringD= QUOTE  * c( (p'\\"'+(1-QUOTE -EOL))^0 )* cerr(QUOTE, "broken string")


	local NegativeSymbol=(MINUS * _ )^-1
	local IntegerCore=NegativeSymbol * DIGIT^1 
	local RationalCore=NegativeSymbol * DIGIT^0 * '.' * #DIGIT* cerr(DIGIT^1,"malformed rational")

	local Integer= c( IntegerCore ) * _
	local Rational=c( RationalCore) * _
	local Exponetional=c( (RationalCore+IntegerCore) * 'e' * cerr(IntegerCore, "malformed exponetional") ) * _
	local HexElem= DIGIT+r'af'+r'AF'
	local Hexdigit = c(p'0x'*cerr(HexElem^1,'malformed hexadecimal'))

	local NumberToken = Hexdigit+Exponetional+Rational+Integer
	local Num=v.Number
	local WS=v.WS
	-- local Boolean= c(TRUE+FALSE)

	local cnil	= cc(nil)

	local function findLine(txt,pos)
		local line=1
		local init=0
		print(pos)
		while true do
			local p1,p2=string.find(txt,'\n', init)
			if not p1 then return line,-1 end
			if p1>pos then
				return line, pos-init
			end
			line=line+1
			init=p2+1
		end
	end

	local function cmark(label) 
		return cmt(0, function(txt, pos, v)
										print(
											string.format('%s @ %d:%d', label or '', findLine(txt, pos))
										)
										print('...' .. string.sub(txt, pos, pos+10) .. '...')
										return pos
									end
								)
	end

	local LineCmt=p'//'*(1-EOL)^0*(EOL+(-p(1)))
	local BlockCmt=p'/*'*(1 - p'*/')^0 *p'*/'

	local COMMENT=LineCmt+BlockCmt

	local function w(pattern)
		return _ * pattern * _
	end

----------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------
	local entry=p{
		'Sprite';
		
		WS	=	(s' \t'+COMMENT+EOL)^0;
		
		Sprite=	WS
			* p'{' *WS / t0('sprite')
			*	v.Version  *WS /tset('version')
			*	v.Images  *WS /tset('images')
			*	v.Modules  *WS /tset('modules')
			*	v.Frames  *WS /tset('frames')
			*	v.Animations  *WS /tset('animations')
			*	v.Tilesets  *WS /tset('tilesets')
			* p'SPRITE_END' *WS
			* '}' *WS
			;

		Number = NumberToken/tonumber;
----------------------------------------------------------------------------------------

		Version= p'VERSION' * _ * Num;
----------------------------------------------------------------------------------------

		Images= ct((WS* v.Image )^0) ;

		Image = p'IMAGE' * _ *(Num + cnil) * _ * StringD * _ *
									(p'ALPHA' * _ * StringD + cnil) * _ *
									(p'TRANSP' * _ * Num + cnil)
						/t4('image','id','file','alpha','transp') 
						;

----------------------------------------------------------------------------------------
		Modules=p'MODULES' * WS * p'{' * WS 
						* ct((WS * v.ModuleBody) ^ 0)
						* ct((WS * v.Mapping) ^ 0)
						* WS * p'}'
						/t2('modules','modules','mappings')
						;

		ModuleBody= 
						p'MD' * w(Num) *
						v.ModuleData * _ * (StringD+cnil) * EOL 
						/t2('module','id','data')
						;

		ModuleData=
				p'MD_IMAGE' * w(Num) * w(Num) * w(Num) * w(Num) * w(Num) 
				/t5('image','id','x','y','w','h')

			+	p'MD_RECT' * w(Num) * w(Num) * w(Num)
				/t3('rect','color','w','h')

			+	p'MD_FILL_RECT' * w(Num) * w(Num) * w(Num)
				/t3('fill_rect','color','w','h')

			+	p'MD_ARC' * w(Num) * w(Num) * w(Num) * w(Num) * w(Num)
				/t5('arc','color','w','h','start','angle')

			+	p'MD_FILL_ARC' * w(Num) * w(Num) * w(Num) * w(Num) * w(Num)
				/t5('fill_arc','color','w','h','start','angle')

			+	p'MD_MARKER' * w(Num) * w(Num) * w(Num)
				/t3('marker','color','w','h')

			+	p'MD_TRIANGLE' * w(Num) * w(Num) * w(Num) * w(Num)
				/t5('triangle','color','x2','y2','x3','y3')

			+	p'MD_FILL_TRIANGLE' * w(Num) * w(Num) * w(Num) * w(Num)
				/t5('fill_triangle','color','x2','y2','x3','y3')
			;

		Mapping=p'MAPPING' * _ * StringD 
					*WS*p'{'*WS
						* Num * WS
						* ct( ( v.MapEntry *WS )^0 )
					*WS*'}'
					/t3('mapping','desc','id','data')
					;

		MapEntry= p'MAP'* ct(w(Num) * w(Num))
					;

----------------------------------------------------------------------------------------
		Frames= ct( (v.Frame * WS ) ^ 0 ) 
						;

		Frame = p'FRAME' * _ * (StringD + cnil)  --desc
					*WS*p'{'*WS
						* w(Num) * WS --id
						* ct((WS * v.FrameRC) ^ 0) --rc
						* ct((WS * v.FrameData) ^ 0) --fm						
					*WS*'}'
					/t4('frame','desc','id','rc','fm')
					;

		FrameRC = p'RC' * w(Num)* w(Num)* w(Num)* w(Num)
						/t4('rc','x1','y1','x2','y2')
						;

		FrameData = p'FM' * w(Num)* w(Num)* w(Num) * (v.FrameFlags+cnil) * _ * (v.FrameBlend+cnil)
						/t5('fm','id', 'ox','oy', 'flags','blend')
						;

		FrameFlags=ct( (_ * p'+'*c(Name) ) ^0 );

		FrameBlend=p'ALPHA'* w(Num)* w(Num) / t2('blend', 'id','alpha');

----------------------------------------------------------------------------------------
		Animations=ct((WS* v.Animation )^0) 
							;

		Animation=p'ANIM' * _ * (StringD + cnil) --desc
						*WS*p'{'*WS
							* w(Num) * EOL  --id
							* ct((WS * v.AnimFrame) ^ 0) --frames
						*WS*'}'
						/t3('animation','desc','id','frames')
						;

		AnimFrame=p'AF' * w(Num) * w(Num) * w(Num) * w(Num) * (v.AnimFrameFlags+cnil) 
							/t5('af','id','time','ox','oy', 'flags')
							;

		AnimFrameFlags=ct( (_ * p'+'*c(Name))^0 );

----------------------------------------------------------------------------------------
		Tilesets= ct( (v.Tileset * WS) ^ 0) ;

		Tileset=p'TILESET' * _ * (StringD+cnil) /t1('tileset','desc') --desc
						*WS*p'{'*WS
							* p'FLAGS' * w(Num) * WS / tset('flags')
							* p'ID' * w(Num) * WS / tset('id')
							* p'TILE_SIZE' * ct(w(Num) * w(Num) ) * WS / tset('tile_size')
							* p'ISO_XPARAMS' * ct(w(Num) * w(Num) ) * WS / tset('iso_xparams')
							* p'ISO_YPARAMS' * ct(w(Num) * w(Num) ) * WS / tset('iso_yparams')
							* p'TILE_VIEW' * w(Num) * WS / tset('tile_view')
							* p'TILE_TYPE' * w(c(Name)) * WS / tset('tile_type')

							* v.TilesetPalette / tset('tileset_palette')

						*WS*'}'						
						;

		TilesetPalette=p'TILESET_PALETTE' * WS
							* p'{' *WS
							* p'PALETTE_SIZE' * ct(w(Num) * w(Num)) * WS--size
							* p'}' *WS
							/ t2('tileset_palette', 'size','data')
		}

----------------------------------------------------------------------------------------
function convertAuroraSprite(filename, outputfile)
	local input=io.open(filename,'r'):read('*all')
	local parsed=L.match(entry, input)
	
	--CONVERSION for faster loading

	local images = {}
	for i, im in ipairs( parsed.images ) do
		--todo: opacity process	
		local filename = string.gsub( im.file, '\\', '/' )
		if filename:sub(1, 2)=='./' then
			filename = filename:sub(3, -1)
		end
		images[i]={
			file = filename,
			alpha = im.alpha,
			transp= im.transp
		}
	end

	local moduleAndFrame={}
	local modules={}
	local moduleImageCount = 0
	for i, m in ipairs( parsed.modules.modules ) do
		moduleAndFrame[ m.id ]=m
		m.id2 = i
		local mm
		local data=m.data
		if data.tag == 'image' then 
			mm={
				type = 'image', 
				rect={data.x, data.y, data.w, data.h},
				image = data.id
			}
		else
			mm={
				type = data.tag,
				color = data.color,
				size = {w, h}
			}
		end
		modules[i] = mm 
	end

	for i, frame in pairs( parsed.frames ) do
		local id = frame.id
		moduleAndFrame[ frame.id ]=frame
	end

	local frames={}
	local partCount=0
	for i, frame in ipairs( parsed.frames ) do
		frame.id2 = i --new id	
		local parts={}
		for j, fm in ipairs(frame.fm) do
			local m = moduleAndFrame[ fm.id ]
			local x, y = fm.ox, fm.oy
			local w, h = 10, 10
			local texrect

			local d=m.data
			if m.tag=='module' then
				w,h = d.w, d.h
			elseif m.tag=='fm' then
				error('TODO:embed fm') --TODO: copy the frame here
			end
			
			local rect = {0, 0, w, h}
			local rot = 0
			for _, flag in ipairs(fm.flags) do
				if flag=='FLIP_X' then
					rect = {rect[3],rect[2],rect[1],rect[4]}
				elseif flag=='FLIP_Y' then
					rect = {rect[1],rect[4],rect[3],rect[2]}
				elseif flag=='ROT_90' then
					rot = 0
				end
			end

			rect = {rect[1]+x,rect[4]+y,rect[3]+x,rect[2]+y}

			parts[j] = {
				rect = rect,
				rot  = rot or false,
				module  = m.id2
			}
			partCount = partCount + 1
		end

		frames[i] = {
			name = frame.desc,
			rc = frame.rc,
			parts = parts,
		}
	end


	local animationNames={}
	local animations={}
	for i, animation in ipairs( parsed.animations ) do

		local namebase=animation.desc or 'null'
		local name=namebase
		local prefix=1
		while animationNames[name] do --auto rename duplicated anim
			name = namebase .. '_' .. prefix
			prefix=prefix+1
		end
		animationNames[name] = true

		local frames={}
		for j, f in ipairs( animation.frames ) do
			local fm= moduleAndFrame[ f.id ]
			frames[j] = {
				flags=f.flags,
				id = fm.id2,
				offset={f.ox, f.oy},
				time = f.time
			}
		end

		animations[i]={
				name=name,
				frames=frames
			}
	end

	local final={
		version = parsed.version,
		images  = images,
		partCount = partCount,
		modules = modules,
		frames = frames,
		animations = animations,
	}

	local file = io.open(outputfile,'w')
	file:write(MOAIJsonParser.encode(final))
	file:close()

	return final
end

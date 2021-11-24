from PIL import Image

def bleeding_image( image ):
	border = 1
	width  = border + image.size[0] + border
	height = border + image.size[1] + border
	out = Image.new(image.mode, (width, height) )
	out.paste(image, (border, border))

	top = out.crop( (0,1,width,2) )
	out.paste( top, (0,0,width,1) )

	bottom = out.crop( (0,height-2,width,height-1) )
	out.paste( bottom, (0,height-1,width,height) )
	
	left = out.crop( (1,0,2,height) )
	out.paste( left, (0,0,1,height) )

	right = out.crop( (width-2,0,width-1,height) )
	out.paste( right, (width-1,0,width,height) )
	return out

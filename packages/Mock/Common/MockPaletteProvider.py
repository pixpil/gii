from gii.qt.controls.ColorPickerWidget import PaletteProvider
from mock import _MOCK, isMockInstance, getMockClassName

class MockPaletteProvider( PaletteProvider ):
	def pullPalettes( self ):
		#read mock palette
		output = []
		lib = _MOCK.getPaletteLibrary()
		for pal in list(lib.palettes.values()):
			items = []
			for col in list(pal.colorList.values()):
				name = col.name
				c    = col.color
				items.append({
						'name': col.name,
						'color': ( c[1], c[2], c[3], c[4] )
					})
			output.append({
				'name' : pal.name,
				'items': items
			})
		return output

	def pushPalettes( self, palettes ):
		lib = _MOCK.getPaletteLibrary()
		lib.clear( lib )
		for pal in palettes:
			p = lib.addPalette( lib )
			p.name = pal[ 'name' ]
			for item in pal[ 'items' ]:
				cname = item[ 'name' ]
				(r,g,b,a) = item[ 'color' ]
				p.addColor( p, cname, r,g,b,a )
		lib.saveConfig( lib )

MockPaletteProvider().setDefault()

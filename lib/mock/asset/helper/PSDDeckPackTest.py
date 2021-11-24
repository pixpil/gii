from PSDDeckPackProject import *
import PSDDeckMTileset
import PSDDeckMQuad
import PSDDeckQuads

import timeit


def test():
	proj = PSDDeckPackProject()
	proj.setDefaultProcessor( 'mquad' )

	proj.loadPSD( 'test/testLarge.decks.psd' )
	proj.save( 'test/', 'testpack', ( 2048, 2048 ) )


duration = timeit.timeit( test, number = 1 )
print('execution:', duration)


# proj.loadPSD( 'test/rotation.decks.psd' )
# proj.save( 'test/', 'rotationTest', ( 2048, 2048 ) )

# proj.loadPSD( 'test/slope.decks.psd' )
# proj.save( 'test/', 'slopeTest', ( 2048, 2048 ) )

# proj.loadPSD( 'test/quadtest.decks.psd' )
# proj.save( 'test/', 'quadtest', ( 1024, 1024 ) )
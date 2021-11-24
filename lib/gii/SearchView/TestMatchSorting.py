from Levenshtein import ratio

def searchScore( name, term ):
	nameU = name.upper()
	termU = term.upper()
	globs = termU.split()
	score = 0
	size = len( name )
	for t in globs:
		pos = nameU.find( t )
		if pos >= 0:
			k = float(pos)/size - 0.5
			score += ( k*k * 0.5 + 0.5 )
		score += ( ratio( t, nameU ) * 0.1 )
	return score


a = [
	'GoodCamera',
	'Camera',
	'CameraImageEffect',
	'CameraImageEffectBloom',
	'CameraImageEffectBlur',
	'CameraImageEffectColorGrading',
	'CameraImageEffectGamma',
	'CameraImageEffectGaussianBlur',
	'CameraImageEffectGrayScale',
	'CameraImageEffectHue',
	'CameraImageEffectInvert',
	'CameraImageEffectMosaic',
	'CameraImageEffectNoise',
	'CameraImageEffectRadialBlur',
	'CameraImageEffectSepia',
	'CameraImageEffectSharpen',
	'CameraImageEffectYUVOffset',
	'CameraManager',
]

for item in a:
	print((item, searchScore( item, 'cam' )))
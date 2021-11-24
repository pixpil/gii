cdef extern from 'freejoy.h' nogil:
	int       JoyCount      ()
	char*     JoyCName      ( int port )
	int       JoyButtonCaps ( int port )
	int       JoyAxisCaps   ( int port )
	int       ReadJoy       ( int port, int* buttons, float* axis )
	int       WriteJoy      ( int port, int channel, float value )

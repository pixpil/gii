// freejoy.h

#ifndef freejoy_h
#define freejoy_h

#if defined(__cplusplus) || defined(c_plusplus)
extern "C" {
#endif


	int   JoyCount      ();
	char* JoyCName      (int port);
	int   JoyButtonCaps (int port);
	int   JoyAxisCaps   (int port);
	int   ReadJoy       (int port,int *buttons,float *axis);
	void  WriteJoy      (int port,int channel,float value);

	enum axisbits {
		JOYX,
		JOYY,
	  JOYZ,
	  JOYR,
	  JOYU,
	  JOYV,
	  JOYYAW,
	  JOYPITCH,
	  JOYROLL,
	  JOYHAT,
	  JOYWHEEL
	 };

#if defined(__cplusplus) || defined(c_plusplus)
}
#endif

#endif

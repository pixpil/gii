from qtpy.QtCore import Qt
import json

output={
	'@': Qt.Key_At,
	'backspace': Qt.Key_Backspace,
	'tab': Qt.Key_Tab,
	'pause': Qt.Key_Pause,
	'escape': Qt.Key_Escape,
	'space': Qt.Key_Space,
	',': Qt.Key_Comma,
	'\'': Qt.Key_QuoteLeft,
	'-': Qt.Key_Minus,
	'.': Qt.Key_Period,
	'slash': Qt.Key_Slash,
	'return': Qt.Key_Return,
	'0': Qt.Key_0,
	'1': Qt.Key_1,
	'2': Qt.Key_2,
	'3': Qt.Key_3,
	'4': Qt.Key_4,
	'5': Qt.Key_5,
	'6': Qt.Key_6,
	'7': Qt.Key_7,
	'8': Qt.Key_8,
	'9': Qt.Key_9,
	':': Qt.Key_Colon,
	';': Qt.Key_Semicolon,
	'=': Qt.Key_Equal,
	'[': Qt.Key_BracketLeft,
	'\\': Qt.Key_Backslash,
	']': Qt.Key_BracketRight,
	'a': Qt.Key_A,
	'b': Qt.Key_B,
	'c': Qt.Key_C,
	'd': Qt.Key_D,
	'e': Qt.Key_E,
	'f': Qt.Key_F,
	'g': Qt.Key_G,
	'h': Qt.Key_H,
	'i': Qt.Key_I,
	'j': Qt.Key_J,
	'k': Qt.Key_K,
	'l': Qt.Key_L,
	'm': Qt.Key_M,
	'n': Qt.Key_N,
	'o': Qt.Key_O,
	'p': Qt.Key_P,
	'q': Qt.Key_Q,
	'r': Qt.Key_R,
	's': Qt.Key_S,
	't': Qt.Key_T,
	'u': Qt.Key_U,
	'v': Qt.Key_V,
	'w': Qt.Key_W,
	'x': Qt.Key_X,
	'y': Qt.Key_Y,
	'z': Qt.Key_Z,
	'delete': Qt.Key_Delete,
	'up': Qt.Key_Up,
	'down': Qt.Key_Down,
	'right': Qt.Key_Right,
	'left': Qt.Key_Left,
	'insert': Qt.Key_Insert,
	'home': Qt.Key_Home,
	'end': Qt.Key_End,
	'pageup': Qt.Key_PageUp,
	'pagedown': Qt.Key_PageDown,
	'f1': Qt.Key_F1,
	'f2': Qt.Key_F2,
	'f3': Qt.Key_F3,
	'f4': Qt.Key_F4,
	'f5': Qt.Key_F5,
	'f6': Qt.Key_F6,
	'f7': Qt.Key_F7,
	'f8': Qt.Key_F8,
	'f9': Qt.Key_F9,
	'f10': Qt.Key_F10,
	'f11': Qt.Key_F11,
	'f12': Qt.Key_F12,
	'f13': Qt.Key_F13,
	'f14': Qt.Key_F14,
	'f15': Qt.Key_F15,
	'numlock': Qt.Key_NumLock,
	'scrolllock': Qt.Key_ScrollLock,
	'shift': Qt.Key_Shift,
	'control': Qt.Key_Control,
	'alt': Qt.Key_Alt,
	'meta': Qt.Key_Meta,
	'sysreq': Qt.Key_SysReq,
	'menu': Qt.Key_Menu
}

def convertKeyCode(k):
	if k>1000:
		return (k&0xff)+(255 - 0x55)
	else:
		return k

print("{")
for k in output:
	code = convertKeyCode(output[k])
	assert (code < 256), (k, code)
	print(("\t[\"%s\"] = %d ;" % (k, code)))
print("}")

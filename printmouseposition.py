import win32api,win32gui,ctypes
import time

pos = (0,0)

while 1:
    pos = win32gui.GetCursorPos()
    print(pos)
    time.sleep(1)

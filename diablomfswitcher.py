import win32api,win32gui,ctypes


offset = (1207,590) #(x,y) position of top left inventory slot
width = 47 #width of each inventory slot

isdown = False
pos = (0,0)

slots = [(0,4), #slots to click, (0,0) is top left, (9,5) is bottom right
         (1,5),
         (2,5),
         (3,5),
         (4,5),
         (4,4),
         (5,5),
         (6,5),
         (7,5),
         (8,5),
         (9,5)]

altslots = [(0,5) #slots that require ALT to be pressed (second ring / offhand)
            ]

while 1:
    pressed = win32api.GetAsyncKeyState(112) # 112 = F1

    if(pressed and (isdown == False)):
        isdown = True
        pos = win32gui.GetCursorPos()

        ctypes.windll.user32.keybd_event(73, 0, 0, 0) # 73 = i
        ctypes.windll.user32.keybd_event(73, 0, 0x2, 0)
        
        for i in slots:
            x = offset[0] + i[0] * width;
            y = offset[1] + i[1] * width;
            ctypes.windll.user32.SetCursorPos(x, y)
        
            ctypes.windll.user32.mouse_event(0x8,0,0,0,0)
            ctypes.windll.user32.mouse_event(0x10,0,0,0,0)
        
        for i in altslots:
            x = offset[0] + i[0] * width;
            y = offset[1] + i[1] * width;
            ctypes.windll.user32.SetCursorPos(x, y)

            ctypes.windll.user32.keybd_event(164, 0, 0, 0)
        
            ctypes.windll.user32.mouse_event(0x8,0,0,0,0)
            ctypes.windll.user32.mouse_event(0x10,0,0,0,0)

            ctypes.windll.user32.keybd_event(164, 0, 0x2, 0)

            
        ctypes.windll.user32.SetCursorPos(pos[0],pos[1])
        ctypes.windll.user32.keybd_event(73, 0, 0, 0)
        ctypes.windll.user32.keybd_event(73, 0, 0x2, 0)
        
    elif(not pressed):
        isdown = False;

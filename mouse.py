import win32gui
from time import sleep

gx = None
gy = None
gw = None
gh = None

def callback(hwnd, extra):
    rect = win32gui.GetWindowRect(hwnd)

    x = rect[0]
    y = rect[1]
    w = rect[2] - x
    h = rect[3] - y

    name = win32gui.GetWindowText(hwnd)

    if not "RuneLite" in name:
        return

    # print("Window %s:" % name)
    print("\tLocation: (%d, %d)" % (x, y))
    print("\t    Size: (%d, %d)" % (w, h))

    global gx
    gx = x
    global gy
    gy = y
    global gw
    gw = w
    global gh
    gh = h

def get_pos():
    win32gui.EnumWindows(callback, None)
    sleep(2)
    
    return (gx, gy, gw, gh)

import win32gui
from time import sleep

gname = None

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

    if not gname in name:
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


def get_window_pos(name):
    global gname
    gname = name

    win32gui.EnumWindows(callback, None)

    tries = 50
    while tries > 0 and (gx is None or gy is None or gw is None or gh is None):
        tries -= 1
        print("Waiting for pos..")
        sleep(0.1)

    if tries <= 0:
        print(f"ERROR: Failed to find window pos for Window: {name}")
        return None

    return gx, gy, gw, gh

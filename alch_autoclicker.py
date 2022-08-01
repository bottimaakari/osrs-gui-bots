import secrets
import keyboard
import pyautogui

# Use system random data source
rng = secrets.SystemRandom()

# Mouse speed limits
mouse_min = 50
mouse_max = 150

# Collect game window info (topleft coords)
window_name = "RuneLite"
window = pyautogui.getWindowsWithTitle(window_name)[0].topleft


def mouse_info():
    pyautogui.mouseInfo()
    exit(0)


def randomized_sleep(minms, maxms):
    tm = rng.randint(minms, maxms) / 1000
    print("Delay for: " + str(tm) + " ms")
    pyautogui.sleep(tm)


def rand_mouse_speed(minms, maxms):
    tm = rng.randint(minms, maxms) / 1000
    print("Mouse speed: " + str(tm) + " ms")
    return tm


def randomized_offset(x, y):
    max_off = 5
    return \
        rng.randint((window.x + x) - max_off, (window.x + x) + max_off), \
        rng.randint((window.y + y) - max_off, (window.y + y) + max_off)


def click_target(x, y):
    pyautogui.moveTo(x, y, rand_mouse_speed(mouse_min, mouse_max))
    pyautogui.leftClick()


def open_spell_menu():
    x, y = randomized_offset(745, 210)
    click_target(x, y)


def click_spell():
    x, y = randomized_offset(718, 328)
    click_target(x, y)


def click_item(item):
    x, y = randomized_offset(item[0], item[1])
    click_target(x, y)


def read_items():
    name = "items.txt"
    file = open(name, "r")

    data = []
    for line in file:
        line = line.strip()
        if line == "" or line[0] == "#":
            continue
        values = line.split(";")
        data.append([int(values[0]), int(values[1]), int(values[2])])

    return data


def on_press_esc(event):
    print("Interrupted.")
    global running
    running = False


# TODO enable for pos info
# mouse_info()

# Key 1 = ESC
# Key 82 = NUMPAD 0
keyboard.on_press_key(1, on_press_esc)

# (ITEM POSX, ITEM POSY, ITEM COUNT)
items = read_items()

running = True
doClickSpell = True
current = 0

# First, ensure spell menu open
open_spell_menu()

# Start looping
while running:
    print(f"Loop: {doClickSpell}")
    randomized_sleep(0, 500)

    if doClickSpell:
        click_spell()
        doClickSpell = False

    elif not doClickSpell:
        if items[current][2] <= 0:
            print(f"Item {current} out. Moving to next..")
            current += 1

        if current >= len(items):
            print("Out of items.")
            break

        click_item(items[current])
        randomized_sleep(1100, 1200)
        items[current][2] -= 1
        doClickSpell = True

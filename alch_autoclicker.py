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
    tm = rng.randint(minms, maxms)
    print(f"Delay for: {tm} ms")
    pyautogui.sleep(tm / 1000)
    return tm


def rand_mouse_speed(minms, maxms):
    tm = rng.randint(minms, maxms)
    print(f"Mouse speed: {tm} ms")
    return tm / 1000


def randomized_offset(x, y):
    max_off = 5
    return \
        rng.randint((window.x + x) - max_off, (window.x + x) + max_off), \
        rng.randint((window.y + y) - max_off, (window.y + y) + max_off)


def click_target(x, y):
    print(f"Click target: ({x}, {y})")
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

running = True
doClickSpell = True
current = 0
last_sleep = None

print("Started. Hit ESC at any time to stop execution.")
print("NOTE: Ensure item details are correctly set in items data file.")

# Sleep for 1.5 sec
randomized_sleep(1500, 1500)

# Key 1 = ESC
# Key 82 = NUMPAD 0
keyboard.on_press_key(1, on_press_esc)

# (ITEM POSX, ITEM POSY, ITEM COUNT)
items = read_items()
print("Read item data from file.")

# First, ensure spell menu open
print("Opening spell menu..")
open_spell_menu()

# Start looping
while running:
    print(f"DoClickSpell: {doClickSpell}")
    last_sleep = randomized_sleep(400, 600)

    if doClickSpell:
        click_spell()
        doClickSpell = False

    else:

        if current >= len(items):
            print("Out of items.")
            break

        if items[current][2] <= 0:
            print(f"Item {current} out. Moving to next..")
            current += 1
            continue

        click_item(items[current])
        randomized_sleep(1400 - last_sleep, 1600 - last_sleep)
        items[current][2] -= 1
        doClickSpell = True

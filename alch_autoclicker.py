import secrets
import threading

import keyboard
import pyautogui


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


def randomized_offset(x, y, use_window=True):
    ox = window.x + x if use_window else x
    oy = window.y + y if use_window else y
    max_off = 5

    return \
        rng.randint(ox - max_off, ox + max_off), \
        rng.randint(oy - max_off, oy + max_off)


def random_movement():
    for i in range(0, rng.randint(0, 5)):
        randomized_sleep(10, 30)
        x, y = randomized_offset(rng.randint(move_min, move_max), rng.randint(move_min, move_max,), use_window=False)
        pyautogui.moveRel(x, y, rand_mouse_speed(30, 60))


def mouse_movement_background(arg):
    while running:
        randomized_sleep(10, 500)
        if not can_move:
            continue
        random_movement()


def click_target(x, y):
    print(f"Click target: ({x}, {y})")

    # Some random mouse movement before action
    # random_movement()

    global can_move
    can_move = False
    pyautogui.moveTo(x, y, rand_mouse_speed(mouse_min, mouse_max))
    pyautogui.leftClick()
    can_move = True

    # Some random mouse movement after action
    # random_movement()


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

# Use system random data source
rng = secrets.SystemRandom()

# Mouse speed limits
mouse_min = 50
mouse_max = 200

move_min = -10
move_max = 10

# Collect game window info (topleft coords)
window_name = "RuneLite"
window = pyautogui.getWindowsWithTitle(window_name)[0].topleft

can_move = True
running = True
doClickSpell = True
current = 0

# Key 1 = ESC
# Key 82 = NUMPAD 0
keyboard.on_press_key(1, on_press_esc)

print("Started. Hit ESC at any time to stop execution.")
print("NOTE: Ensure item details are correctly set in items data file.")

# Sleep for 1.5 sec
randomized_sleep(1500, 1500)

# (ITEM POSX, ITEM POSY, ITEM COUNT)
items = read_items()
print("Read item data from file.")

move_thread = threading.Thread(target=mouse_movement_background, name="bg_mouse_movement", args=(None,))
move_thread.start()

# First, ensure spell menu open
print("Opening spell menu..")
open_spell_menu()

# Start looping
while running:
    last_sleep = randomized_sleep(200, 400)

    print(f"DoClickSpell: {doClickSpell}")

    # 20 % chance for ensuring spell menu is open
    # before clicking the spell
    if doClickSpell and rng.random() <= 0.2:
        open_spell_menu()
        continue

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

move_thread.join()

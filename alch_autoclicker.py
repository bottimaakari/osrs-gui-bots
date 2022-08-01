import secrets
import keyboard
import pyautogui

rng = secrets.SystemRandom()

mouse_min = 100
mouse_max = 300


def mouse_info():
    pyautogui.mouseInfo()
    exit(0)


def random_sleep(minms, maxms):
    tm = rng.randint(minms, maxms) / 1000
    print("Delay for: " + str(tm) + " ms")
    pyautogui.sleep(tm)


def rand_mouse_speed(minms, maxms):
    tm = rng.randint(minms, maxms) / 1000
    print("Mouse speed: " + str(tm) + " ms")
    return tm


def open_spell_menu():
    x = rng.randint(1575, 1585)
    y = rng.randint(992, 1002)
    pyautogui.moveTo(x, y, rand_mouse_speed(mouse_min, mouse_max))
    pyautogui.leftClick()


def click_spell():
    x = rng.randint(1545, 1555)
    y = rng.randint(1105, 1115)
    pyautogui.moveTo(x, y, rand_mouse_speed(mouse_min, mouse_max))
    pyautogui.leftClick()


def click_item(item):
    x = rng.randint(item[0] - 5, item[0] + 5)
    y = rng.randint(item[1] - 5, item[1] + 5)
    pyautogui.moveTo(x, y, rand_mouse_speed(mouse_min, mouse_max))
    pyautogui.leftClick()


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
items = [
    [1455, 1113, 25],
    [1500, 1113, 30],
    [1540, 1113, 36]
]

running = True
doClickSpell = True
current = 0

# First, ensure spell menu open
open_spell_menu()

# Start looping
while running:
    print(f"Loop: {doClickSpell}")
    random_sleep(0, 500)

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
        random_sleep(1200, 1400)
        items[current][2] -= 1
        doClickSpell = True

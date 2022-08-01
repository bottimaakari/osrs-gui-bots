import secrets
import threading

import keyboard
import pyautogui

import clicker_common


def randomized_offset(x, y, use_window=True):
    w = window().topleft

    ox = w.x + x if use_window else x
    oy = w.y + y if use_window else y

    return \
        rng.randint(ox - max_off, ox + max_off), \
        rng.randint(oy - max_off, oy + max_off)


def mouse_movement_background():
    print("BG Thread started.")
    while running:
        clicker_common.rand_sleep(rng, 10, 800)

        if not can_move:
            continue

        for i in range(0, rng.randint(0, 6)):
            clicker_common.rand_sleep(rng, 10, 50)
            if not can_move:
                continue
            x, y = randomized_offset(rng.randint(move_min, move_max), rng.randint(move_min, move_max), use_window=False)
            pyautogui.moveRel(x, y, clicker_common.rand_mouse_speed(rng, 30, 60))

    print("BG Thread exiting.")


def hover_target(x, y):
    print(f"Hover target: ({x}, {y})")
    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, mouse_min, mouse_max))


def click_target(x, y):
    print(f"Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    global can_move
    can_move = False

    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, mouse_min, mouse_max))
    pyautogui.leftClick()

    can_move = True


def open_spellbook():
    loc = tuple(map(int, settings['spellbook_location'].split(',')))
    x, y = randomized_offset(loc[0], loc[1])
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 50, 500)
    # Recalculate x,y and click the target
    x, y = randomized_offset(loc[0], loc[1])
    click_target(x, y)


def click_spell():
    loc = tuple(map(int, settings['spell_location'].split(',')))
    x, y = randomized_offset(loc[0], loc[1])
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 1200, 1300)
    # Recalculate x,y and click the target
    x, y = randomized_offset(loc[0], loc[1])
    click_target(x, y)


def click_item(item):
    x, y = randomized_offset(item[0], item[1])
    # Calculate x,y and alredy hover on the target
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 30, 500)
    # Recalculate x,y and click the target
    x, y = randomized_offset(item[0], item[1])
    click_target(x, y)


def window():
    return clicker_common.window(window_name)


def interrupt(event):
    print("Interrupted.")
    global running
    running = False


# Use system random data source
rng = secrets.SystemRandom()

try:
    settings_file = "settings.txt"

    # Read configuration file
    settings = clicker_common.read_settings(settings_file)

    # Collect game window info (topleft coords)
    window_name = str(settings["window_title"])

    try:
        window = pyautogui.getWindowsWithTitle(window_name)[0].topleft
    except IndexError as ex:
        print("ERROR: Game client window was not detected. Ensure the game client is running first.")
        raise ex

    mouse_info = settings['mouse_info'] == 'True'

    if mouse_info:
        print(f"TopLeft corner location: {window}")
        pyautogui.mouseInfo()
        exit(0)

    # Mouse speed limits
    mouse_min = int(settings['mouse_min'])
    mouse_max = int(settings['mouse_max'])

    # Random movement offset limits
    move_min = int(settings['rand_min'])
    move_max = int(settings['rand_max'])

    # Maximum precise target offset
    max_off = int(settings['max_off'])

    # Key 1 = ESC
    # Key 82 = NUMPAD 0
    keyboard.on_press_key(1, interrupt)

    print("Started. Hit ESC at any time to stop execution.")
    print("NOTE: Ensure settings are correctly defined in settings file.")
    print("NOTE: Ensure item details are correctly set in items data file.")
    print("NOTE: Please do not move the mouse at all after the program has been started.")

    items_file = settings['items_file']

    # Read inventory data file
    # (ITEM POSX, ITEM POSY, ITEM COUNT)
    inventory = clicker_common.read_inventory(items_file)

    if len(inventory) <= 0:
        print(f"ERROR: No items found in items file ({items_file}). Ensure items configured correctly first. See the "
              f"items example file for reference.")
        raise ValueError("No items defined in items file.")

    print("Read item data from items file.")

    can_move = True
    running = True
    do_click_spell = True
    current = 0

    # Initial sleep to have time to react
    print("Waiting 3 seconds..")
    clicker_common.rand_sleep(rng, 3000, 3000)

    move_thread = threading.Thread(target=mouse_movement_background, name="bg_mouse_movement")
    move_thread.start()

    # First, ensure spell menu open
    print("Opening spell menu..")
    open_spellbook()

    # Start looping
    while running:
        # Must sleep enough between the moves
        # should be close to a constant value
        clicker_common.rand_sleep(rng, 50, 80)

        print(f"do_click_spell: {do_click_spell}")

        # 33 % chance for ensuring spell menu is open
        # before clicking the spell
        if do_click_spell and rng.random() <= float(settings['spellbook_prob']):
            open_spellbook()

        if do_click_spell:
            click_spell()
            do_click_spell = False
            continue

        if current >= len(inventory):
            print("Out of items.")
            interrupt(None)
            break

        if inventory[current][2] <= 0:
            print(f"Item {current} out. Moving to next..")
            current += 1
            continue

        click_item(inventory[current])
        inventory[current][2] -= 1
        do_click_spell = True

    # Gracefully let the bg thread to exit
    move_thread.join()

    print("Sleeping 5 seconds before exiting..")
    clicker_common.rand_sleep(rng, 5000, 5000)

except Exception as e:
    print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
    print(e)
    print("SLEEPING 10 SECONDS BEFORE EXITING..")
    clicker_common.rand_sleep(rng, 10000, 10000)

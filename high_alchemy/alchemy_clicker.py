import secrets
import threading

import keyboard
import pyautogui

import clicker_common


def mouse_movement_background():
    print("BG Thread started.")
    while running:
        clicker_common.rand_sleep(rng, 10, 900, debug_mode)

        if not can_move:
            continue

        for i in range(0, rng.randint(0, 8)):
            clicker_common.rand_sleep(rng, 10, 50, debug_mode)
            if not running or not can_move:
                break
            x, y = clicker_common.randomized_offset(rng,
                                                    rng.randint(move_min, move_max),
                                                    rng.randint(move_min, move_max),
                                                    max_off,
                                                    debug=debug_mode
                                                    )
            pyautogui.moveRel(x, y, clicker_common.rand_mouse_speed(rng, 30, 90, debug_mode))

    print("BG Thread terminated.")


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
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 50, 500, debug_mode)
    # Recalculate x,y and click the target
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    click_target(x, y)


def click_spell():
    loc = tuple(map(int, settings['spell_location'].split(',')))
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 1200, 1300, debug_mode)
    # Recalculate x,y and click the target
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    click_target(x, y)


def click_item(item):
    x, y = clicker_common.randomized_offset(rng, item[0], item[1], max_off, window_name, debug_mode)
    # Calculate x,y and alredy hover on the target
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 30, 500, debug_mode)
    # Recalculate x,y and click the target
    x, y = clicker_common.randomized_offset(rng, item[0], item[1], max_off, window_name, debug_mode)
    click_target(x, y)


def window():
    return clicker_common.window(window_name)


# Catches key interrupt events
# Gracefully erminates the program
def interrupt(ev):
    print("Program interrupted.")
    global running
    running = False
    print("Possibly still waiting for a sleep to finish..")


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

    # Debug prints etc.
    debug_mode = settings['debug_mode'].lower() == 'true'

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

    # Probability to open the spellbook menu
    spellbook_prob = float(settings['spellbook_prob'])

    # Filename of the items file
    items_file = settings['items_file']

    interrupt_key = int(settings['interrupt_key'])

    # From this point on, catch any interruption caused by special key
    keyboard.on_press_key(interrupt_key, interrupt)

    print("Started. Hit ESC at any time to stop execution.")
    print("NOTE: Ensure settings are correctly defined in settings file.")
    print("NOTE: Ensure item details are correctly set in items data file.")
    print("NOTE: Please do not move the mouse at all after the program has been started.")

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
    print("Waiting 4 seconds..")
    clicker_common.rand_sleep(rng, 4000, 4000)

    move_thread = threading.Thread(target=mouse_movement_background, name="bg_mouse_movement")
    move_thread.start()

    # First, ensure spell menu open
    print("Opening spell menu..")
    open_spellbook()

    # Start looping
    while running:
        # Must sleep enough between the moves
        # should be close to a constant value
        clicker_common.rand_sleep(rng, 50, 90)

        if not running:
            break

        print(f"do_click_spell: {do_click_spell}")

        # 33 % chance for ensuring spell menu is open
        # before clicking the spell
        if do_click_spell and rng.random() <= spellbook_prob:
            open_spellbook()

        if do_click_spell:
            click_spell()
            do_click_spell = False
            continue

        while current < len(inventory) and inventory[current][2] <= 0:
            print("Out of current item. Moving to next item.")
            current += 1

        if current >= len(inventory):
            print("Out of items.")
            running = False
            break

        else:
            print("Use item.")
            click_item(inventory[current])
            inventory[current][2] -= 1

        do_click_spell = True

    # Gracefully let the bg thread to exit
    if move_thread.is_alive():
        print("Waiting for BG thread to stop..")
        move_thread.join()

except Exception as e:
    print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
    print(e)

input("Press ENTER to EXIT..")

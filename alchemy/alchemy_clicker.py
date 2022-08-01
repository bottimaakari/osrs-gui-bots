import threading

import keyboard
import pyautogui

import clicker_common
import globvals


def hover_target(x, y):
    print(f"Hover target: ({x}, {y})")
    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max))


def left_click_target(x, y):
    print(f"Left Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    globvals.can_move = False

    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max, debug_mode))
    pyautogui.leftClick()

    globvals.can_move = True


def hover_click(location, delay_min, delay_max):
    # Calculate randomized-off x,y and hover to the target first
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    hover_target(x, y)

    # Wait for a while before next action
    clicker_common.rand_sleep(rng, delay_min, delay_max, debug_mode)

    # Recalculate random-off x,y and click the target
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    left_click_target(x, y)


def hotkey_press(key):
    print(f"Press Key: {key}")
    clicker_common.rand_sleep(rng, 50, 400, debug_mode)
    pyautogui.press(key, presses=1)


def focus_window():
    print("Focus on game window.")
    hover_click((50, 5), 50, 400)


def open_spellbook():
    print("Open spellbook menu.")
    hotkey_press(spellbook_key)


def click_spell():
    print("Click spell.")
    loc = tuple(map(int, settings['spell_location'].split(',')))
    hover_click(loc, 1200, 1300)


def click_item(item):
    print("Click item.")
    hover_click((item[0], item[1]), 50, 400)


def window():
    return clicker_common.window(window_name)


# Catches key interrupt events
# Gracefully erminates the program
def interrupt(ev):
    print("Program interrupted.")
    globvals.running = False
    print("Possibly still waiting for a sleep to finish..")


try:
    # Use system random data source
    rng = clicker_common.init_rng()

    settings_file = "settings.txt"

    # Read configuration file
    settings = clicker_common.read_settings(settings_file)

    # Collect game window info (topleft coords)
    window_name = str(settings["window_title"])

    try:
        window()
    except Exception as ex:
        print("ERROR: Game client window was not detected. Ensure the game client is running first.")
        print("Also check that window title is correct in settings.")
        raise ex

    # Debug prints etc.
    debug_mode = settings['debug_mode'].lower() == 'true'

    mouse_info = settings['mouse_info'].lower() == 'true'

    if mouse_info:
        print(f"TopLeft corner location: {window}")
        pyautogui.mouseInfo()
        exit(0)

    # Mouse speed limits
    speed_min = int(settings['mouse_min'])
    speed_max = int(settings['mouse_max'])

    # Random movement offset limits
    move_min = int(settings['rand_min'])
    move_max = int(settings['rand_max'])

    # Maximum precise target offset
    max_off = int(settings['max_off'])

    # Probability to open the spellbook menu
    spellbook_prob = float(settings['spellbook_prob'])

    # Filename of the items file
    items_file = settings['items_file']

    # Keyboard event key codes
    interrupt_key = int(settings['interrupt_key'])

    # UI Shortcut keys
    spellbook_key = settings['spellbook_key']

    # From this point on, catch any interruption caused by special key
    keyboard.on_press_key(interrupt_key, interrupt)

    # Print instructions on start before start delay
    clicker_common.print_start_info(interrupt_key)

    # Initial sleep for user to have time to react on startup
    clicker_common.start_delay(rng)

    # Read inventory data file
    # (ITEM POSX, ITEM POSY, ITEM COUNT)
    inventory = clicker_common.read_inventory(items_file)

    if len(inventory) <= 0:
        print(f"ERROR: No items found in items file ({items_file}). Ensure items configured correctly first. See the "
              f"items example file for reference.")
        raise ValueError("No items defined in items file.")

    print("Read item data from items file.")

    globvals.running = True
    globvals.can_move = True

    do_click_spell: bool = True
    current: int = 0

    # Print instructions on start before start delay
    clicker_common.print_start_info(interrupt_key)

    # Initial sleep for user to have time to react on startup
    clicker_common.start_delay(rng)

    global_timer = clicker_common.Timer()

    move_thread = threading.Thread(
        target=clicker_common.mouse_movement_background,
        name="bg_mouse_movement",
        args=(rng, move_min, move_max, max_off, debug_mode)
    )
    move_thread.start()

    # Ensure game window focused
    focus_window()

    # First, ensure spell menu open
    open_spellbook()

    # Start looping
    while globvals.running:
        # Must sleep enough between the moves
        # should be close to a constant value
        clicker_common.rand_sleep(rng, 50, 90)

        if not globvals.running:
            break

        print(f"Click spell: {do_click_spell}")

        # 33 % chance for ensuring spell menu is open
        # before clicking the spell
        if do_click_spell and rng.random() < spellbook_prob:
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

        clicker_common.print_status(global_timer)

    # Gracefully let the bg thread to exit
    if move_thread.is_alive():
        print("Waiting for BG thread(s) to stop..")
        move_thread.join()

except Exception as e:
    globvals.running = False
    print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
    print(e)

input("Press ENTER to EXIT..")

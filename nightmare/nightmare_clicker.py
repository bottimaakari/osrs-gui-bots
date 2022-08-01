import operator
import secrets
import threading

import keyboard
import pyautogui

import clicker_common


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

    print("BG Thread terminated.")


def randomized_offset(x, y, use_window=True):
    w = window().topleft

    ox = w.x + x if use_window else x
    oy = w.y + y if use_window else y

    return \
        rng.randint(ox - max_off, ox + max_off), \
        rng.randint(oy - max_off, oy + max_off)


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


def window():
    return clicker_common.window(window_name)


def ensure_inventory_open():
    loc = tuple(map(int, settings['inv_location'].split(',')))
    x, y = randomized_offset(loc[0], loc[1])
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 50, 500)
    x, y = randomized_offset(loc[0], loc[1])
    click_target(x, y)


def click_prayer():
    loc = tuple(map(int, settings['prayer_location'].split(',')))
    x, y = randomized_offset(loc[0], loc[1])
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 50, 500)
    x, y = randomized_offset(loc[0], loc[1])
    click_target(x, y)
    clicker_common.rand_sleep(rng, wmin, wmax)  # Special sleep between double click
    x, y = randomized_offset(loc[0], loc[1])
    click_target(x, y)


def click_special_attack():
    loc = tuple(map(int, settings['special_location'].split(',')))
    x, y = randomized_offset(loc[0], loc[1])
    hover_target(x, y)
    clicker_common.rand_sleep(rng, 50, 500)
    x, y = randomized_offset(loc[0], loc[1])
    click_target(x, y)


def click_item(target):
    x, y = randomized_offset(target[0], target[1])  # Get randomized coords to the target item
    hover_target(x, y)  # Move to the target
    clicker_common.rand_sleep(rng, 50, 500)  # Sleep for random time
    x, y = randomized_offset(target[0], target[1])  # Get randomized coords to the target item
    click_target(x, y)  # Click the target


def move_outside_window():
    w = window()

    tl = w.topleft
    tr = w.topright
    bl = w.bottomleft
    br = w.bottomright

    targets = [
        tuple(map(operator.add, (tl.x, tl.y), (-50, -50))),
        tuple(map(operator.add, (tr.x, tr.y), (50, -50))),
        tuple(map(operator.add, (bl.x, bl.y), (-50, 50))),
        tuple(map(operator.add, (br.x, br.y), (50, 50))),
    ]

    target = rng.choice(targets)
    clicker_common.rand_sleep(rng, 50, 500)
    hover_target(target[0], target[1])


# Catches key interrupt events
# Gracefully erminates the program
def interrupt(ev):
    print("Program interrupted.")
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
        window()
    except IndexError as ex:
        print("ERROR: Game client window was not detected. Ensure the game client is running first.")
        raise ex

    mouse_info = settings['mouse_info'].lower() == 'true'

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

    # Loop interval
    loop_min = int(settings['loop_min'])
    loop_max = int(settings['loop_max'])

    wmin = int(settings['click_min'])
    wmax = int(settings['click_max'])

    # Maximum precise target offset
    max_off = int(settings['max_off'])

    # Probability to open inventory tab
    inv_prob = float(settings['inv_menu_prob'])

    # Probability to click an item
    item_prob = float(settings['item_prob'])

    # Special attack probability
    special_prob = float(settings['special_prob'])

    item_time = int(settings['item_time_min'])
    special_time = int(settings['special_time_min'])

    use_prayer = settings['use_prayer'].lower() == "true"
    use_item = settings['use_items'].lower() == "true"
    use_special = settings['use_special'].lower() == "true"

    # Key 1 = ESC
    # Key 82 = NUMPAD 0
    keyboard.on_press_key(1, interrupt)

    print("Started. Hit ESC at any time to stop execution.")
    print("NOTE: Ensure settomgs are correctly defined in settings file.")
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

    running = True
    can_move = True
    current = 0

    # Initial sleep to have time to react
    print("Waiting 3 seconds before starting..")
    clicker_common.rand_sleep(rng, 3000, 3000)

    move_thread = threading.Thread(target=mouse_movement_background, name="bg_mouse_movement")
    move_thread.start()

    # Double click the prayer button to reset regeneration
    if use_prayer:
        print("Double click quick prayer.")
        click_prayer()

    # Initially, ensure mouse is outside game window
    move_outside_window()

    # Collect timestamp right before starting to loop
    # Time point at start in ms
    global_timer = clicker_common.Timer()
    item_timer = clicker_common.Timer()
    special_timer = clicker_common.Timer()

    # Start looping
    while running:
        # TODO longer max (allow regenerate
        # Sleep for a random time, at maximum the time the health regenerates
        can_move = False
        clicker_common.rand_sleep(rng, loop_min, loop_max)
        can_move = True

        if not running:
            break

        # Double click the prayer button to reset regeneration
        if use_prayer:
            print("Double click quick prayer.")
            click_prayer()

        # TODO rock cake

        if use_special and special_timer.elapsed() >= special_time and rng.random() <= special_prob:
            special_timer.reset()
            print("Click special attack.")
            click_special_attack()

        # If the probability was hit, ensure the inventory tab is open
        if rng.random() <= inv_prob:
            print("Ensure inventory open.")
            ensure_inventory_open()

        # After Looped 4 times in a row, click the first item available
        if use_item and item_timer.elapsed() >= item_time and rng.random() <= item_prob:
            item_timer.reset()
            print("Click next non-empty item if available.")

            while inventory[current][2] <= 0 and current < len(inventory):
                print("Out of current item. Moving to next item.")
                current += 1

            if current >= len(inventory):
                print("Out of items.")
            else:
                click_item(inventory[current])
                inventory[current][2] -= 1

        move_outside_window()

        print(f"Total elapsed: {(global_timer.elapsed() / 1000):0.2f} seconds.")

    # Gracefully let the bg thread to exit
    move_thread.join()

    print("Sleep 5 seconds before exiting..")
    clicker_common.rand_sleep(rng, 5000, 5000)

except Exception as e:
    print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
    print(e)
    print("SLEEP 10 SECONDS BEFORE EXITING..")
    clicker_common.rand_sleep(rng, 10000, 10000)

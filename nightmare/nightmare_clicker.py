import operator
import secrets
import threading

import keyboard
import pyautogui

import clicker_common


def mouse_movement_background():
    print("BG Thread started.")
    while running:
        clicker_common.rand_sleep(rng, 10, 1000, debug_mode)

        if not can_move:
            continue

        for i in range(0, rng.randint(0, rng.randint(0, 8))):
            clicker_common.rand_sleep(rng, 20, 50, debug_mode)
            if not running or not can_move:
                break
            x, y = clicker_common.randomized_offset(rng,
                                                    rng.randint(move_min, move_max),
                                                    rng.randint(move_min, move_max),
                                                    max_off,
                                                    debug=debug_mode
                                                    )
            pyautogui.moveRel(x, y, clicker_common.rand_mouse_speed(rng, 30, 80, debug_mode))

    print("BG Thread terminated.")


def hover_target(x, y):
    print(f"Hover target: ({x}, {y})")
    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, mouse_min, mouse_max, debug_mode))


def left_click_target(x, y):
    print(f"Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    global can_move
    can_move = False

    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, mouse_min, mouse_max, debug_mode))
    pyautogui.leftClick()

    can_move = True


def hover_click(location):
    # Calculate randomized-off x,y and hover to the target first
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    hover_target(x, y)

    # Wait for a while before next action
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)

    # Recalculate random-off x,y and click the target
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    left_click_target(x, y)


def focus_window():
    print("Focus on game window.")
    hover_click((50, 5))


def ensure_inventory_open():
    print("Ensure inventory open.")
    loc = tuple(map(int, settings['inv_location'].split(',')))
    hover_click(loc)


def click_special_attack():
    print("Click special attack.")
    loc = tuple(map(int, settings['special_location'].split(',')))
    hover_click(loc)


def click_item(target):
    print("Use item.")
    hover_click((target[0], target[1]))


def click_snd_item(target):
    print("Use secondary item.")
    hover_click((target[0], target[1]))


def click_prayer():
    print("Double Click quick prayer.")
    loc = tuple(map(int, settings['prayer_location'].split(',')))
    hover_click(loc)
    clicker_common.rand_sleep(rng, wmin, wmax, debug_mode)  # Special sleep between double click
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    left_click_target(x, y)


def move_outside_window():
    print("Move mouse outside game window.")
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

    # Choose a random game window corner
    target = rng.choice(targets)
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)

    # Hover away from the screen to the desired corner
    hover_target(target[0], target[1])

    # Additionally, set the focus away from the game window
    left_click_target(target[0], target[1])


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
        window()
    except IndexError as ex:
        print("ERROR: Game client window was not detected. Ensure the game client is running first.")
        raise ex

    mouse_info = settings['mouse_info'].lower() == 'true'

    if mouse_info:
        print(f"TopLeft corner location: {window().topleft}")
        pyautogui.mouseInfo()
        exit(0)

    # Debug prints etc.
    debug_mode = settings['debug_mode'].lower() == 'true'

    interrupt_key = int(settings['interrupt_key'])

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

    action_min = int(settings['action_min'])
    action_max = int(settings['action_max'])

    # Maximum precise target offset
    max_off = int(settings['max_off'])

    # Probability to open inventory tab
    inv_prob = float(settings['inv_menu_prob'])

    # Probability to click an item
    item_prob = float(settings['item_prob'])

    # Probability to click an item
    snd_prob = float(settings['snd_item_prob'])

    # Special attack probability
    special_prob = float(settings['special_prob'])

    item_time = int(settings['item_time_min'])
    snd_time = int(settings['snd_item_time_min'])
    special_time = int(settings['special_time_min'])
    run_max = int(settings['max_run_time'])

    act_start = settings['act_start'].lower() == "true"

    use_prayer = settings['use_prayer'].lower() == "true"
    use_item = settings['use_items'].lower() == "true"
    use_snd_item = settings['use_snd_items'].lower() == "true"
    use_special = settings['use_special'].lower() == "true"

    items_file = settings['items_file']
    snd_file = settings['snd_items_file']

    # Read inventory data file
    # (ITEM POSX, ITEM POSY, ITEM COUNT)
    inventory = None
    if use_item:
        inventory = clicker_common.read_inventory(items_file)
        if len(inventory) <= 0:
            print(
                f"ERROR: No items found in items file ({items_file}). Ensure items configured correctly first. See the "
                f"items example file for reference.")
            raise ValueError("No items defined in items file.")
        else:
            print("Read item data from items file.")

    snd_inv = None
    if use_snd_item:
        snd_inv = clicker_common.read_inventory(snd_file)
        if len(snd_inv) <= 0:
            print(
                f"ERROR: No items found in secondary items file ({snd_file}). Ensure items configured correctly first. "
                f"See the items example file for reference.")
            raise ValueError("No items defined in items file.")
        else:
            print("Read item data from secondary items file.")

    running = True
    can_move = True
    current = 0
    snd_current = 0

    move_thread = threading.Thread(target=mouse_movement_background, name="bg_mouse_movement")

    # Key 1 = ESC
    # Key 82 = NUMPAD 0
    # Key 41 = §
    keyboard.on_press_key(interrupt_key, interrupt)

    print(f"Started. Hit key with code {interrupt_key} at any time to stop execution.")
    print("NOTE: Ensure settomgs are correctly defined in settings file.")
    print("NOTE: Ensure item details are correctly set in items data file.")
    print("NOTE: Please do not move the mouse at all after the program has been started.")

    # Initial sleep to have time to react
    print("Waiting 4 seconds before starting..")
    clicker_common.rand_sleep(rng, 4000, 4000)  # debug=True

    # Before each operation, check that we are still running
    # and not interrupted (running == True)

    # Start the bg mouse movement thread
    if running:
        move_thread.start()
        print("Mouse movement BG thread started.")

    if running and act_start:
        print("Running actions at program start..")

        # Ensure game window focused
        if running:
            focus_window()

        # First, ensure inventory tab is open
        if running:
            ensure_inventory_open()

        # Double click the prayer button to reset regeneration
        if running and use_prayer:
            click_prayer()

        # use the special attack
        if running and use_special:
            click_special_attack()

        # No need for using the primary item
        # at start (typically absorb potion)
        # because points already full

        # Use the snd item (e.g. stats potion)
        if running and use_snd_item:
            click_snd_item(snd_inv[snd_current])
            snd_inv[snd_current][2] -= 1

        # Initially, ensure mouse is outside game window
        if running:
            move_outside_window()

    # Timers for keeping track when allowed to commit next actions
    # Separate timer for each task
    global_timer = clicker_common.Timer()
    item_timer = clicker_common.Timer()
    snd_timer = clicker_common.Timer()
    special_timer = clicker_common.Timer()


    def prayer_action():
        # Double click the prayer button to reset regeneration
        if use_prayer:
            click_prayer()


    def special_action():
        if use_special and special_timer.elapsed() >= special_time and rng.random() <= special_prob:
            special_timer.reset()
            click_special_attack()


    def item_action():
        # Click the first item available, if is enabled, if odds hit, if minimum time passed
        item_rnd = rng.random()
        if debug_mode:
            print(f"Item: {use_item}|{item_timer.elapsed()}|{item_time}|{item_rnd}|{item_prob}")
        if use_item and item_timer.elapsed() >= item_time and item_rnd <= item_prob:
            item_timer.reset()
            print("Click next non-empty item if available.")

            global current
            while current < len(inventory) and inventory[current][2] <= 0:
                print("Out of current item. Moving to next item.")
                current += 1

            if current >= len(inventory):
                print("Out of items.")
            else:
                click_item(inventory[current])
                inventory[current][2] -= 1


    def snd_item_action():
        # Click the first secondary item available, if is enabled, if odds hit, if minimum time passed
        snd_rnd = rng.random()
        if debug_mode:
            print(f"Secondary item: {use_snd_item}|{snd_timer.elapsed()}|{snd_time}|{snd_rnd}|{snd_prob}")
        if use_snd_item and snd_timer.elapsed() >= snd_time and snd_rnd <= snd_prob:
            snd_timer.reset()
            print("Click next non-empty secondary item if available.")

            global snd_current
            while snd_current < len(snd_inv) and snd_inv[snd_current][2] <= 0:
                print("Out of current item. Moving to next item.")
                snd_current += 1

            if snd_current >= len(snd_inv):
                print("Out of items.")
            else:
                click_snd_item(snd_inv[snd_current])
                snd_inv[snd_current][2] -= 1


    # Setup actions
    actions = []
    if use_special:
        actions.append(special_action)
    if use_item:
        actions.append(item_action)
    if use_snd_item:
        actions.append(snd_item_action)

    # Start looping
    while running:
        # Sleep for a random time, at maximum the time the health regenerates
        can_move = False
        clicker_common.rand_sleep(rng, loop_min, loop_max)  # debug=True
        can_move = True

        if not running:
            print("Not running anymore.")
            break

        if global_timer.elapsed() >= run_max:
            print("Max runtime reached. Stopping.")
            running = False
            break

        # If the probability was hit, ensure the inventory tab is open
        if rng.random() <= inv_prob:
            ensure_inventory_open()

        # Always do prayer action first (timing!)
        # Excluded from the action list
        prayer_action()

        # Commit rest of the actions in random order
        rng.shuffle(actions)
        for action in actions:
            action()

        # Finally, move the cursor outside the game window
        move_outside_window()

        secs = global_timer.elapsed() / 1000

        hrs = int(secs / 3600)
        mins = int(secs / 60 - hrs * 60)
        secs = int(secs - hrs * 3600 - mins * 60)

        print(f"Total elapsed: {hrs} hrs | {mins} mins | {secs} secs.")

    # Gracefully let the bg thread to exit
    if move_thread.is_alive():
        print("Waiting for BG thread to stop..")
        move_thread.join()

except Exception as e:
    running = False
    print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
    print(e)

input("Press ENTER to EXIT..")

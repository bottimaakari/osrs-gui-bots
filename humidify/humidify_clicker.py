import datetime
import operator
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
    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max, debug_mode))


def left_click_target(x, y):
    print(f"Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    global can_move
    can_move = False

    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max, debug_mode))
    pyautogui.leftClick()

    can_move = True


def right_click_target(x, y):
    print(f"Right Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    global can_move
    can_move = False

    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max, debug_mode))
    pyautogui.rightClick()

    can_move = True


def press_key(key):
    print(f"Press Key: {key}")
    pyautogui.press(key, presses=1)


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
    clicker_common.rand_sleep(rng, 50, 500, debug_mode)
    hover_target(target[0], target[1])


def open_spellbook():
    print("Ensure spellbook open.")
    loc = tuple(map(int, settings['spellbook_location'].split(',')))
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    # Recalculate x,y and click the target
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    left_click_target(x, y)


def click_spell():
    print("Click spell.")
    loc = tuple(map(int, settings['spell_location'].split(',')))
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    # Recalculate x,y and click the target
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    left_click_target(x, y)


def open_bank():
    print("Open bank.")
    loc = tuple(map(int, settings['bank_location'].split(',')))
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    left_click_target(x, y)


def deposit_item():
    print("Deposit item(s).")
    loc = tuple(map(int, settings['deposit_location'].split(',')))
    offset = int(settings['deposit_offset'])

    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    right_click_target(x, y)

    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1] + offset, 1, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1] + offset, 1, window_name, debug_mode)
    left_click_target(x, y)


def withdraw_item():
    print("Withdraw item(s).")
    loc = tuple(map(int, settings['withdraw_location'].split(',')))
    offset = int(settings['withdraw_offset'])

    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1], max_off, window_name, debug_mode)
    right_click_target(x, y)

    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1] + offset, 1, window_name, debug_mode)
    hover_target(x, y)
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    x, y = clicker_common.randomized_offset(rng, loc[0], loc[1] + offset, 1, window_name, debug_mode)
    left_click_target(x, y)


def close_bank():
    print("Close bank screen.")
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    press_key("ESC")


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
    speed_min = int(settings['mouse_speed_min'])
    speed_max = int(settings['mouse_speed_max'])

    # Random movement offset limits
    move_min = int(settings['rand_min'])
    move_max = int(settings['rand_max'])

    # Action delays
    action_min = int(settings['action_min'])
    action_max = int(settings['action_max'])

    # Loop interval - time to wait before every cycle
    wait_min = int(settings['wait_min'])
    wait_max = int(settings['wait_max'])

    wmin = int(settings['click_min'])
    wmax = int(settings['click_max'])

    # Maximum precise target offset
    max_off = int(settings['max_off'])

    run_max = int(settings['max_run_time'])

    act_start = settings['act_start'].lower() == "true"

    running = True
    can_move = True
    item_left = int(settings['item_left'])

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

    # Timers for keeping track when allowed to commit next actions
    # Separate timer for each task
    global_timer = clicker_common.Timer()

    # Before each operation, check that we are still running
    # and not interrupted (running == True)

    # Start the bg mouse movement thread
    if running:
        move_thread.start()
        print("Mouse movement BG thread started.")

    if running and act_start:
        print("Running actions at program start..")

        if running:
            open_spellbook()
            open_bank()
            if item_left < 27:
                print("Out of item. Exiting.")
                running = False
            withdraw_item()
            item_left -= 27
            close_bank()
            click_spell()

    # Start looping
    while running:
        # Wait until spell action finished
        clicker_common.rand_sleep(rng, wait_min, wait_max)  # debug=True for longer delay

        if not running:
            break

        if global_timer.elapsed() >= run_max:
            print("Max runtime reached. Stopping.")
            running = False
            break

        open_bank()

        deposit_item()

        if item_left < 27:
            print("Out of item. Exiting.")
            running = False
            break

        # Withdraw 27 items from bank
        withdraw_item()
        item_left -= 27

        close_bank()

        click_spell()

        secs = global_timer.elapsed() / 1000
        hrs = int(secs / 3600)
        mins = int(secs / 60 - hrs * 60)
        secs = int(secs - hrs * 3600 - mins * 60)
        print(f"Total elapsed: {hrs} hrs | {mins} mins | {secs} secs.")
        print(f"Timestamp: {datetime.datetime.now()}")

    # Gracefully let the bg thread to exit
    if move_thread.is_alive():
        print("Waiting for BG thread to stop..")
        move_thread.join()

except Exception as e:
    running = False
    print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
    print(e)

input("Press ENTER to EXIT..")

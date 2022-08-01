import datetime
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
    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max, debug_mode))


def left_click_target(x, y):
    print(f"Left Click target: ({x}, {y})")

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


def hotkey_press(key):
    print(f"Press Key: {key}")
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)
    pyautogui.press(key, presses=1)


def hover(location):
    # Wait for a while before next action
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)

    # Calculate randomized-off x,y and hover to the target first
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    hover_target(x, y)


def hover_click(location):
    # Calculate randomized-off x,y and hover to the target first
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    hover_target(x, y)

    # Wait for a while before next action
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)

    # Recalculate random-off x,y and click the target
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    left_click_target(x, y)


def hover_context_click(location, offset):
    # Calculate randomized-off x,y and hover to the target first
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    hover_target(x, y)

    # Wait for a while before next action
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)

    # Right click the target to open context menu
    x, y = clicker_common.randomized_offset(rng, location[0], location[1], max_off, window_name, debug_mode)
    right_click_target(x, y)

    # Hover to the context menu offset
    x, y = clicker_common.randomized_offset(rng, location[0], location[1] + offset, 1, window_name, debug_mode)
    hover_target(x, y)

    # Wait a bit before proceeding
    clicker_common.rand_sleep(rng, action_min, action_max, debug_mode)

    # Finally, click the menu option in the predefined offset
    x, y = clicker_common.randomized_offset(rng, location[0], location[1] + offset, 1, window_name, debug_mode)
    left_click_target(x, y)


def focus_window():
    print("Focus on game window.")
    hover_click((50, 5))


def click_spell():
    print("Click spell.")
    loc = tuple(map(int, settings['spell_location'].split(',')))
    hover_click(loc)

    loc = tuple(map(int, settings['bank_location'].split(',')))
    hover(loc)


def open_bank():
    print("Open bank.")
    loc = tuple(map(int, settings['bank_location'].split(',')))
    hover_click(loc)


def deposit_item():
    print("Deposit item(s).")
    loc = tuple(map(int, settings['deposit_location'].split(',')))

    if left_banking:
        hover_click(loc)
    else:
        off = int(settings['deposit_offset'])
        hover_context_click(loc, off)


def withdraw_item():
    print("Withdraw item(s).")
    loc = tuple(map(int, settings['withdraw_location'].split(',')))

    if left_banking:
        hover_click(loc)
    else:
        off = int(settings['withdraw_offset'])
        hover_context_click(loc, off)


def open_spellbook():
    print("Ensure spellbook open.")
    hotkey_press(spellbook_key)


def close_interface():
    print("Close current interface.")
    clicker_common.rand_sleep(rng, close_min, close_max, debug_mode)
    hotkey_press(close_key)


def take_break():
    print("Taking a break.")
    clicker_common.rand_sleep(rng, break_min, break_max, debug=True)  # Longer break -> debug output


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
    except Exception as ex:
        print("ERROR: Game client window was not detected. Ensure the game client is running first.")
        print("Also check that window title is correct in settings.")
        raise ex

    mouse_info = settings['mouse_info'].lower() == 'true'

    if mouse_info:
        print(f"TopLeft corner location: {window().topleft}")
        pyautogui.mouseInfo()
        exit(0)

    # Debug prints etc.
    debug_mode = settings['debug_mode'].lower() == 'true'

    # Key codes
    interrupt_key = int(settings['interrupt_key'])

    # UI Shortcut keys
    close_key = settings['close_menu_key']
    spellbook_key = settings['spellbook_key']

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

    # Additional delay before closing an interface
    close_min = int(settings['close_min'])
    close_max = int(settings['close_max'])

    # Random breaks interval
    break_min = int(settings['break_min'])
    break_max = int(settings['break_max'])

    # Probability to take a random break
    break_prob = float(settings['break_prob'])

    # Break timer elapsed min
    break_time = int(settings['break_time_min'])

    # Maximum precise target offset
    max_off = int(settings['max_off'])

    run_max = int(settings['max_run_time'])

    act_start = settings['act_start'].lower() == "true"

    left_banking = settings['left_click_banking'].lower() == "true"

    running = True
    can_move = True
    break_taken = False

    item_left = int(settings['item_left'])
    item_take = int(settings['item_take'])

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
    break_timer = clicker_common.Timer()

    # Before each operation, check that we are still running
    # and not interrupted (running == True)

    # Start the bg mouse movement thread
    if running:
        move_thread.start()
        print("Mouse movement BG thread started.")

    if running and act_start:
        print("Running actions at program start..")
        if running:
            focus_window()
        if running:
            close_interface()
        if running:
            open_bank()
        if running:
            if item_left < item_take:
                print("Out of item(s). Exiting.")
                running = False
            else:
                withdraw_item()
                item_left -= item_take
        if running:
            close_interface()
        if running:
            open_spellbook()
        if running:
            click_spell()


    def break_action():
        break_rnd = rng.random()
        global break_taken, can_move
        # If break not yet taken in this loop, enough time from previous break passed, and random number hits prob
        if not break_taken and break_timer.elapsed() >= break_time and break_rnd < break_prob:
            break_timer.reset()
            can_move = False
            take_break()
            can_move = True
            break_taken = True


    # Start looping
    while running:
        # Reset break status every iteration
        break_taken = False

        if not running:
            print("Not running anymore.")
            break

        # Wait until spell action finished
        clicker_common.rand_sleep(rng, wait_min, wait_max)  # debug=True for longer delay

        if not running:
            print("Not running anymore.")
            break

        if global_timer.elapsed() >= run_max:
            print("Max runtime reached. Stopping.")
            running = False
            break

        open_bank()
        break_action()

        if not running:
            print("Not running anymore.")
            break

        deposit_item()
        break_action()

        if not running:
            print("Not running anymore.")
            break

        # Withdraw 27 items from bank
        if item_left < item_take:
            print("Out of item(s). Exiting.")
            running = False
            break
        withdraw_item()
        item_left -= item_take
        break_action()

        if not running:
            print("Not running anymore.")
            break

        close_interface()
        break_action()

        if not running:
            print("Not running anymore.")
            break

        open_spellbook()
        break_action()

        if not running:
            print("Not running anymore.")
            break

        click_spell()
        break_action()

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

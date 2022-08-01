import datetime
import threading

import keyboard
import pyautogui

import clicker_common
import globvals


def hover_target(x, y):
    print(f"Hover target: ({x}, {y})")
    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max, debug_mode))


def left_click_target(x, y):
    print(f"Left Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    globvals.can_move = False

    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max, debug_mode))
    pyautogui.leftClick()

    globvals.can_move = True


def right_click_target(x, y):
    print(f"Right Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    globvals.can_move = False

    pyautogui.moveTo(x, y, clicker_common.rand_mouse_speed(rng, speed_min, speed_max, debug_mode))
    pyautogui.rightClick()

    globvals.can_move = True


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
    hover_click(spell_location)

    print("Hover on bank.")
    hover(bank_location)


def open_bank():
    print("Open bank.")
    hover_click(bank_location)


def deposit_item():
    print("Deposit item(s).")

    if left_banking:
        print("Using left click.")
        hover_click(deposit_location)
    else:
        print("Using right click context menu.")
        hover_context_click(deposit_location, deposit_offset)


def withdraw_item():
    print("Withdraw item(s).")

    if left_banking:
        hover_click(withdraw_location)
    else:
        hover_context_click(withdraw_location, withdraw_offset)


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
    globvals.running = False
    print("Possibly still waiting for a sleep to finish..")


try:
    # Use quantumrandom as random data source for better entropy
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

    spell_location = tuple(map(int, settings['spell_location'].split(',')))
    bank_location = tuple(map(int, settings['bank_location'].split(',')))
    deposit_location = tuple(map(int, settings['deposit_location'].split(',')))
    withdraw_location = tuple(map(int, settings['withdraw_location'].split(',')))

    deposit_offset = int(settings['deposit_offset'])
    withdraw_offset = int(settings['withdraw_offset'])

    item_left = int(settings['item_left'])
    item_take = int(settings['item_take'])

    globvals.running = True
    globvals.can_move = True
    globvals.break_taken = False

    move_thread = threading.Thread(
        target=clicker_common.mouse_movement_background,
        name="bg_mouse_movement",
        args=(rng, move_min, move_max, max_off, debug_mode)
    )
    move_thread.start()

    # Key 1 = ESC
    # Key 82 = NUMPAD 0
    # Key 41 = §
    keyboard.on_press_key(interrupt_key, interrupt)

    # Print instructions on start before start delay
    clicker_common.print_start_info(interrupt_key)

    # Initial sleep for user to have time to react on startup
    clicker_common.start_delay(rng)

    # Timers for keeping track when allowed to commit next actions
    # Separate timer for each task
    global_timer = clicker_common.Timer()
    break_timer = clicker_common.Timer()

    # Before each operation, check that we are still running
    # and not interrupted (running == True)

    # Start the bg mouse movement thread
    if globvals.running:
        move_thread.start()
        print("Mouse movement BG thread started.")

    if globvals.running and act_start:
        print("Running actions at program start..")
        if globvals.running:
            focus_window()
        if globvals.running:
            close_interface()
        if globvals.running:
            open_bank()
        if globvals.running:
            if item_left < item_take:
                print("Out of item(s). Exiting.")
                globvals.running = False
            else:
                withdraw_item()
                item_left -= item_take
        if globvals.running:
            close_interface()
        if globvals.running:
            open_spellbook()
        if globvals.running:
            click_spell()


    def break_action():
        # If break not yet taken in this loop, enough time from previous break passed, and random number hits prob
        if not globvals.break_taken and break_timer.elapsed() >= break_time and rng.random() < break_prob:
            break_timer.reset()
            globvals.can_move = False
            take_break()
            globvals.can_move = True
            globvals.break_taken = True


    # Start looping
    while globvals.running:
        # Reset break status every iteration
        globvals.break_taken = False

        if not globvals.running:
            print("Not running anymore.")
            break

        # Wait until spell action finished
        clicker_common.rand_sleep(rng, wait_min, wait_max)  # debug=True for longer delay

        if not globvals.running:
            print("Not running anymore.")
            break

        if global_timer.elapsed() >= run_max:
            print("Max runtime reached. Stopping.")
            globvals.running = False
            break

        open_bank()
        break_action()

        if not globvals.running:
            print("Not running anymore.")
            break

        deposit_item()
        break_action()

        if not globvals.running:
            print("Not running anymore.")
            break

        # Withdraw 27 items from bank
        if item_left < item_take:
            print("Out of item(s). Exiting.")
            globvals.running = False
            break
        withdraw_item()
        item_left -= item_take
        break_action()

        if not globvals.running:
            print("Not running anymore.")
            break

        close_interface()
        break_action()

        if not globvals.running:
            print("Not running anymore.")
            break

        open_spellbook()
        break_action()

        if not globvals.running:
            print("Not running anymore.")
            break

        click_spell()
        break_action()

        clicker_common.print_status(global_timer)

    # Gracefully let the bg thread to exit
    if move_thread.is_alive():
        print("Waiting for BG thread to stop..")
        move_thread.join()

except Exception as e:
    globvals.running = False
    print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
    print(e)

input("Press ENTER to EXIT..")

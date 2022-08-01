import atexit

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


def take_break():
    print("Taking a break.")
    clicker_common.rand_sleep(rng, break_min, break_max, debug=True)  # Longer break -> debug output


def window():
    return clicker_common.window(window_name)


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


if __name__ == '__main__':
    try:
        # Register a custom exit handler
        # To make sure things happen after everything else is done
        atexit.register(clicker_common.exit_handler)

        # Use quantumrandom as random data source for better entropy
        rng = clicker_common.init_rng()

        settings_file: str = "settings.txt"

        # Read configuration file
        settings: dict[str, str] = clicker_common.read_settings(settings_file)

        # Collect game window info (topleft coords)
        window_name: str = str(settings["window_title"])

        # Check if mouse info mode enabled in settings
        if bool(settings['mouse_info'].lower() == 'true'):
            print(f"TopLeft corner location: {window().topleft}")
            print("Tip: To get correct relative position, calculate: target.x/y - topLeft.x/y")
            pyautogui.mouseInfo()
            exit(0)

        # Ensure game window is detected
        clicker_common.window(window_name)

        # Debug prints etc.
        debug_mode: bool = settings['debug_mode'].lower() == 'true'

        # Key codes
        interrupt_key: int = int(settings['interrupt_key'])
        pause_key: int = int(settings['pause_key'])

        # UI Shortcut keys
        close_key: str = settings['close_menu_key']
        spellbook_key: str = settings['spellbook_key']

        # Mouse speed limits
        speed_min: int = int(settings['mouse_speed_min'])
        speed_max: int = int(settings['mouse_speed_max'])

        # Random movement offset limits
        move_min: int = int(settings['rand_min'])
        move_max: int = int(settings['rand_max'])

        # Action delays
        action_min: int = int(settings['action_min'])
        action_max: int = int(settings['action_max'])

        # Loop interval - time to wait before every cycle
        wait_min: int = int(settings['wait_min'])
        wait_max: int = int(settings['wait_max'])

        # Additional delay before closing an interface
        close_min: int = int(settings['close_min'])
        close_max: int = int(settings['close_max'])

        # Random breaks interval
        break_min: int = int(settings['break_min'])
        break_max: int = int(settings['break_max'])

        # Probability to take a random break
        break_prob: float = float(settings['break_prob'])

        # Break timer elapsed min
        break_time: int = int(settings['break_time_min'])

        # Maximum precise target offset
        max_off: int = int(settings['max_off'])

        run_max: int = int(settings['max_run_time'])

        act_start: bool = settings['act_start'].lower() == "true"

        left_banking: bool = settings['left_click_banking'].lower() == "true"

        spell_location: tuple = tuple(map(int, settings['spell_location'].split(',')[:2]))
        bank_location: tuple = tuple(map(int, settings['bank_location'].split(',')[:2]))
        deposit_location: tuple = tuple(map(int, settings['deposit_location'].split(',')[:2]))
        withdraw_location: tuple = tuple(map(int, settings['withdraw_location'].split(',')[:2]))

        deposit_offset: int = int(settings['deposit_offset'])
        withdraw_offset: int = int(settings['withdraw_offset'])

        item_left: int = int(settings['item_left'])
        item_take: int = int(settings['item_take'])

        globvals.running = True
        globvals.can_move = True

        move_thread = clicker_common.create_movement_thread(
            rng, move_min, move_max, max_off, debug_mode
        )

        keyboard.on_press_key(interrupt_key, clicker_common.interrupt_handler)
        keyboard.on_press_key(pause_key, clicker_common.pause_handler)

        # Print instructions on start before start delay
        clicker_common.print_start_info(interrupt_key)

        # Initial sleep for user to have time to react on startup
        clicker_common.start_delay(rng)

        # Timers for keeping track when allowed to commit next actions
        # Separate timer for each task
        global_timer: clicker_common.Timer = clicker_common.Timer()
        break_timer: clicker_common.Timer = clicker_common.Timer()

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
            # If enough time from previous break passed, and random number hits prob
            if break_timer.elapsed() >= break_time and rng.random() < break_prob:
                break_timer.reset()
                globvals.can_move = False
                take_break()
                globvals.can_move = True


        def pause_action():
            # Disable random movement during pause
            globvals.can_move = False
            while globvals.paused:
                if not globvals.running:
                    break
                # Only sleep 1 sec per loop to minimize response delay
                clicker_common.rand_sleep(rng, 1000, 1000, debug_mode)
            globvals.can_move = True


        # Start looping
        while globvals.running:
            pause_action()
            if not globvals.running:
                break

            # Wait until spell action finished
            clicker_common.rand_sleep(rng, wait_min, wait_max, debug=True)

            pause_action()
            if not globvals.running:
                break

            if global_timer.elapsed() >= run_max:
                print("Max runtime reached. Stopping.")
                globvals.running = False
                break

            open_bank()
            break_action()

            pause_action()
            if not globvals.running:
                break

            deposit_item()
            break_action()

            pause_action()
            if not globvals.running:
                break

            # Withdraw 27 items from bank
            if item_left < item_take:
                print("Out of item(s). Exiting.")
                globvals.running = False
                break
            withdraw_item()
            item_left -= item_take
            break_action()

            pause_action()
            if not globvals.running:
                break

            close_interface()
            break_action()

            pause_action()
            if not globvals.running:
                break

            open_spellbook()
            break_action()

            pause_action()
            if not globvals.running:
                break

            click_spell()

            clicker_common.print_status(global_timer)

            break_action()

        # END WHILE
        print("Main loop stopped.")

        # Cleanup resources
        del rng

        # Gracefully let the bg thread to exit
        if move_thread.is_alive():
            print("Waiting for BG thread to stop..")
            move_thread.join()

    except Exception as e:
        globvals.running = False
        print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
        print(e)

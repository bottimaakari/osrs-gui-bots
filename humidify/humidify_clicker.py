import atexit

import keyboard
import pyautogui

import clicker_framework
import globvals

if __name__ == '__main__':
    try:
        # Register a custom exit handler
        # To make sure things happen after everything else is done
        atexit.register(clicker_framework.exit_handler)

        # Use quantumrandom as random data source for better entropy
        rng = clicker_framework.init_rng()

        settings_file: str = "settings.txt"

        # Read configuration file
        settings: dict[str, str] = clicker_framework.read_settings(settings_file)

        # Collect game window info (top left coords)
        window_name: str = str(settings["window_title"])

        # Ensure game window is detected
        clicker_framework.window(window_name)

        # Check if mouse info mode enabled in settings
        if bool(settings['mouse_info'].lower() == 'true'):
            print(f"TopLeft corner location: {clicker_framework.window(window_name).topleft}")
            print("Tip: To get correct relative position, calculate: target.x/y - topLeft.x/y")
            pyautogui.mouseInfo()
            exit(0)

        # Debug prints etc.
        debug_mode: bool = settings['debug_mode'].lower() == 'true'

        # Key codes
        interrupt_key: int = int(settings['interrupt_key'])
        pause_key: int = int(settings['pause_key'])

        # UI Shortcut keys
        close_key: str = settings['close_menu_key']
        spell_book_key: str = settings['spell_book_key']

        # Mouse speed limits
        speed_min: int = int(settings['mouse_speed_min'])
        speed_max: int = int(settings['mouse_speed_max'])

        # Random movement offset limits
        rand_min: int = int(settings['rand_min'])
        rand_max: int = int(settings['rand_max'])

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
        break_time_min: int = int(settings['break_time_min'])

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

        item_take: int = int(settings['item_take'])

        globvals.item_left = int(settings['item_left'])
        globvals.running = True
        globvals.can_move = True

        common_args = {
            'rng': rng,
            'action_min': action_min,
            'action_max': action_max,
            'speed_min': speed_min,
            'speed_max': speed_max,
            'close_min': close_min,
            'close_max': close_max,
            'max_off': max_off,
            'window_name': window_name,
            'debug': debug_mode
        }

        keyboard.on_press_key(interrupt_key, clicker_framework.interrupt_handler)
        keyboard.on_press_key(pause_key, clicker_framework.pause_handler)

        # Print instructions on start before start delay
        clicker_framework.print_start_info(interrupt_key)

        # Initial sleep for user to have time to react on startup
        clicker_framework.start_delay(rng)

        # Timers for keeping track when allowed to commit next actions
        # Separate timer for each task
        global_timer: clicker_framework.Timer = clicker_framework.Timer()
        break_timer: clicker_framework.Timer = clicker_framework.Timer()

        move_thread = clicker_framework.init_movement_thread(rand_min, rand_max, **common_args)

        # Before each operation, check that we are still running
        # and not interrupted (running == True)

        # Start the bg mouse movement thread
        if globvals.running:
            move_thread.start()

        if globvals.running and act_start:
            print("Running actions at program start..")
            clicker_framework.pause_action(**common_args)
            if globvals.running:
                clicker_framework.focus_window(**common_args)
                clicker_framework.pause_action(**common_args)
            if globvals.running:
                clicker_framework.close_interface(close_key, **common_args)
                clicker_framework.pause_action(**common_args)
            # ACTION LOOP BEGINS HERE
            if globvals.running:
                clicker_framework.open_location(bank_location, **common_args)
                clicker_framework.pause_action(**common_args)
            if globvals.running:
                clicker_framework.withdraw_item(withdraw_location, withdraw_offset, left_banking, item_take, **common_args)
                clicker_framework.pause_action(**common_args)
            if globvals.running:
                clicker_framework.close_interface(close_key, **common_args)
                clicker_framework.pause_action(**common_args)
            if globvals.running:
                clicker_framework.open_menu(spell_book_key, **common_args)
                clicker_framework.pause_action(**common_args)
            if globvals.running:
                clicker_framework.click_spell(spell_location, bank_location, **common_args)
                clicker_framework.pause_action(**common_args)

        # Start looping
        while globvals.running:
            clicker_framework.pause_action(**common_args)
            if not globvals.running:
                break

            # Wait until spell action finished
            clicker_framework.rand_sleep(wait_min, wait_max, **{**common_args, 'debug': True})

            clicker_framework.pause_action(**common_args)
            if not globvals.running:
                break

            if global_timer.elapsed() >= run_max:
                print("Max runtime reached. Stopping.")
                globvals.running = False
                break

            # ACTION LOOP BEGINS HERE
            clicker_framework.open_location(bank_location, **common_args)
            clicker_framework.break_action(break_min, break_max, break_time_min, break_prob, break_timer, **common_args)

            clicker_framework.pause_action(**common_args)
            if not globvals.running:
                break

            clicker_framework.deposit_item(deposit_location, deposit_offset, left_banking, deposit_all=False,
                                           **common_args)
            clicker_framework.break_action(break_min, break_max, break_time_min, break_prob, break_timer, **common_args)

            clicker_framework.pause_action(**common_args)
            if not globvals.running:
                break

            # Withdraw items from bank
            clicker_framework.withdraw_item(withdraw_location, withdraw_offset, left_banking, item_take, **common_args)
            clicker_framework.break_action(break_min, break_max, break_time_min, break_prob, break_timer, **common_args)

            clicker_framework.pause_action(**common_args)
            if not globvals.running:
                break

            clicker_framework.close_interface(close_key, **common_args)
            clicker_framework.break_action(break_min, break_max, break_time_min, break_prob, break_timer, **common_args)

            clicker_framework.pause_action(**common_args)
            if not globvals.running:
                break

            clicker_framework.open_menu(spell_book_key, **common_args)
            clicker_framework.break_action(break_min, break_max, break_time_min, break_prob, break_timer, **common_args)

            clicker_framework.pause_action(**common_args)
            if not globvals.running:
                break

            clicker_framework.click_spell(spell_location, bank_location, **common_args)

            # At the end of the loop, print the status first right after last action
            # before rolling break dice to get status printed e.g. just before a very long break
            clicker_framework.print_status(global_timer)

            clicker_framework.break_action(break_min, break_max, break_time_min, break_prob, break_timer, **common_args)

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
        print("FATAL EXCEPTION OCCURRED DURING SCRIPT EXECUTION:")
        if type(e) == KeyError:
            print("Detected KeyError - Ensure all settings are correctly set with valid values.")
            print(f"Setting that caused the issue: {e} (Check that it is set and is valid in the settings file.)")
        elif type(e) == ValueError:
            print("Detected ValueError - Ensure all settings have valid values set (e.g. string, integer, boolean..)")
            print(f"The following error message might be helpful for detecting what caused the issue: {e!r}")
        else:
            print("Could not determine error cause.")
            print(f"Error message: {e!r}")

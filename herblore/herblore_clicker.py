import atexit

import keyboard
import pyautogui

import clicker_common
import globvals

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

        # Collect game window info (top left coords)
        window_name: str = str(settings["window_title"])

        # Ensure game window is detected
        clicker_common.window(window_name)

        # Check if mouse info mode enabled in settings
        if bool(settings['mouse_info'].lower() == 'true'):
            print(f"TopLeft corner location: {clicker_common.window(window_name).topleft}")
            print("Tip: To get correct relative position, calculate: target.x/y - topLeft.x/y")
            pyautogui.mouseInfo()
            exit(0)

        # Debug prints etc.
        debug_mode: bool = settings['debug_mode'].lower() == 'true'

        # Key codes
        interrupt_key: int = int(settings['interrupt_key'])
        pause_key: int = int(settings['pause_key'])

        # UI Shortcut keys
        close_key = settings['close_menu_key']
        inventory_key = settings['inventory_key']
        confirm_key = settings['confirm_key']

        # Mouse speed limits
        speed_min = int(settings['mouse_speed_min'])
        speed_max = int(settings['mouse_speed_max'])

        # Random movement offset limits
        rand_min = int(settings['rand_min'])
        rand_max = int(settings['rand_max'])

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

        # Script max run time
        run_max = int(settings['max_run_time'])

        snd_deposit = settings['snd_deposit'].lower() == "true"
        act_start = settings['act_start'].lower() == "true"
        left_banking = settings['left_click_banking'].lower() == "true"
        idle_move = settings['idle_movement'].lower() == "true"

        # Location coordinates for click & hover targets
        bank_location: tuple = tuple(map(int, settings['bank_location'].split(',')[:2]))

        fst_combine_location: tuple = tuple(map(int, settings['combine_location'].split(',')[:2]))
        snd_combine_location: tuple = tuple(map(int, settings['snd_combine_location'].split(',')[:2]))

        fst_withdraw_location: tuple = tuple(map(int, settings['withdraw_location'].split(',')[:2]))
        snd_withdraw_location: tuple = tuple(map(int, settings['snd_withdraw_location'].split(',')[:2]))

        fst_deposit_location: tuple = tuple(map(int, settings['deposit_location'].split(',')[:2]))
        snd_deposit_location: tuple = tuple(map(int, settings['snd_deposit_location'].split(',')[:2]))

        withdraw_offset: int = int(settings['withdraw_offset'])
        snd_withdraw_offset: int = int(settings['snd_withdraw_offset'])

        deposit_offset: int = int(settings['deposit_offset'])
        snd_deposit_offset: int = int(settings['snd_deposit_offset'])

        # Items management
        item1_take: int = int(settings['item1_take'])
        item2_take: int = int(settings['item2_take'])

        # Configure global (shared) variables
        globvals.item_left = int(settings['item1_left'])
        globvals.item2_left = int(settings['item2_left'])
        globvals.running = True
        globvals.can_move = True
        globvals.paused = False

        common = {
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

        move_thread = clicker_common.init_movement_thread(rand_min, rand_max, **common)

        # Before each operation, check that we are still running
        # and not interrupted (running == True)

        # Start the bg mouse movement thread
        if globvals.running:
            move_thread.start()
            print("Mouse movement BG thread started.")

        if globvals.running and act_start:
            print("Running actions at program start..")
            clicker_common.pause_action(**common)
            if globvals.running:
                clicker_common.focus_window(**common)
                clicker_common.pause_action(**common)
            if globvals.running:
                clicker_common.close_interface(close_key, **common)
                clicker_common.pause_action(**common)
            if globvals.running:
                clicker_common.open_location(bank_location, **common)
                clicker_common.pause_action(**common)
            if globvals.running:
                clicker_common.withdraw_items(fst_withdraw_location, withdraw_offset, item1_take, snd_withdraw_location,
                                              snd_withdraw_offset, item2_take, left_banking, **common)
                clicker_common.pause_action(**common)
            if globvals.running:
                clicker_common.close_interface(close_key, **common)
                clicker_common.pause_action(**common)
            if globvals.running:
                clicker_common.open_menu(inventory_key, **common)
                clicker_common.pause_action(**common)
            if globvals.running:
                clicker_common.combine_items(fst_combine_location, snd_combine_location, **common)
                clicker_common.pause_action(**common)
            if globvals.running:
                clicker_common.confirm_action(confirm_key, bank_location, **common)
                clicker_common.pause_action(**common)

        # Start looping
        while globvals.running:
            clicker_common.pause_action(**common)
            if not globvals.running:
                break

            # Wait until spell action finished
            globvals.can_move = idle_move
            clicker_common.rand_sleep(wait_min, wait_max, **{**common, 'debug': True})
            globvals.can_move = True

            clicker_common.pause_action(**common)
            if not globvals.running:
                break

            if global_timer.elapsed() >= run_max:
                print("Max runtime reached. Stopping.")
                globvals.running = False
                break

            # ACTION LOOP BEGINS HERE

            clicker_common.open_location(bank_location, **common)
            clicker_common.break_action(break_min, break_max, break_time, break_prob, break_timer, **common)

            clicker_common.pause_action(**common)
            if not globvals.running:
                break

            clicker_common.deposit_items(fst_deposit_location, deposit_offset, snd_deposit_location, snd_deposit_offset,
                                         left_banking, deposit_all=True, **common)
            clicker_common.break_action(break_min, break_max, break_time, break_prob, break_timer, **common)

            clicker_common.pause_action(**common)
            if not globvals.running:
                break

            # Withdraw 27 items from bank
            clicker_common.withdraw_items(fst_withdraw_location, withdraw_offset, item1_take, snd_withdraw_location,
                                          snd_withdraw_offset, item2_take, left_banking, **common)
            clicker_common.break_action(break_min, break_max, break_time, break_prob, break_timer, **common)

            clicker_common.pause_action(**common)
            if not globvals.running:
                break

            clicker_common.close_interface(close_key, **common)
            clicker_common.break_action(break_min, break_max, break_time, break_prob, break_timer, **common)

            clicker_common.pause_action(**common)
            if not globvals.running:
                break

            clicker_common.open_menu(inventory_key, **common)
            clicker_common.break_action(break_min, break_max, break_time, break_prob, break_timer, **common)

            clicker_common.pause_action(**common)
            if not globvals.running:
                break

            clicker_common.combine_items(fst_combine_location, snd_combine_location, **common)
            clicker_common.break_action(break_min, break_max, break_time, break_prob, break_timer, **common)

            clicker_common.pause_action(**common)
            if not globvals.running:
                break

            clicker_common.confirm_action(confirm_key, bank_location, **common)

            clicker_common.print_status(global_timer)

            # Do possible breaking right status info print to keep track of script runtime
            clicker_common.break_action(break_min, break_max, break_time, break_prob, break_timer, **common)

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

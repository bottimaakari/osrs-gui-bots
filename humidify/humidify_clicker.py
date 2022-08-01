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

        # Collect game window info (topleft coords)
        window_name: str = str(settings["window_title"])

        # Check if mouse info mode enabled in settings
        if bool(settings['mouse_info'].lower() == 'true'):
            print(f"TopLeft corner location: {clicker_common.window(window_name).topleft}")
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
        spell_book_key: str = settings['spellbook_key']

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

        item_take: int = int(settings['item_take'])

        globvals.item_left = int(settings['item_left'])
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

        common_args = {
            'rng': rng,
            'max_off': max_off,
            'action_min': action_min,
            'action_max': action_max,
            'speed_min': speed_min,
            'speed_max': speed_max,
            'close_min': close_min,
            'close_max': close_max,
            'window_name': window_name,
            'debug': debug_mode
        }

        # Before each operation, check that we are still running
        # and not interrupted (running == True)

        # Start the bg mouse movement thread
        if globvals.running:
            move_thread.start()
            print("Mouse movement BG thread started.")

        if globvals.running and act_start:
            print("Running actions at program start..")
            clicker_common.pause_action(rng, debug_mode)
            if globvals.running:
                clicker_common.focus_window(**common_args)
                clicker_common.pause_action(rng, debug_mode)
            if globvals.running:
                clicker_common.close_interface(close_key, **common_args)
                clicker_common.pause_action(rng, debug_mode)
            # ACTION LOOP BEGINS HERE
            if globvals.running:
                clicker_common.open_bank(bank_location, **common_args)
                clicker_common.pause_action(rng, debug_mode)
            if globvals.running:
                clicker_common.withdraw_item(withdraw_location, withdraw_offset, left_banking, item_take, **common_args)
                clicker_common.pause_action(rng, debug_mode)
            if globvals.running:
                clicker_common.close_interface(close_key, **common_args)
                clicker_common.pause_action(rng, debug_mode)
            if globvals.running:
                clicker_common.open_spell_book(spell_book_key, **common_args)
                clicker_common.pause_action(rng, debug_mode)
            if globvals.running:
                clicker_common.click_spell(spell_location, bank_location, **common_args)
                clicker_common.pause_action(rng, debug_mode)

        # Start looping
        while globvals.running:
            clicker_common.pause_action(rng, debug_mode)
            if not globvals.running:
                break

            # Wait until spell action finished
            clicker_common.rand_sleep(rng, wait_min, wait_max, debug=True)

            clicker_common.pause_action(rng, debug_mode)
            if not globvals.running:
                break

            if global_timer.elapsed() >= run_max:
                print("Max runtime reached. Stopping.")
                globvals.running = False
                break

            # ACTION LOOP BEGINS HERE
            clicker_common.open_bank(bank_location, **common_args)
            clicker_common.break_action(rng, break_timer, break_time, break_prob, break_min, break_max)

            clicker_common.pause_action(rng, debug_mode)
            if not globvals.running:
                break

            clicker_common.deposit_item(deposit_location, deposit_offset, left_banking, **common_args)
            clicker_common.break_action(rng, break_timer, break_time, break_prob, break_min, break_max)

            clicker_common.pause_action(rng, debug_mode)
            if not globvals.running:
                break

            # Withdraw items from bank
            clicker_common.withdraw_item(withdraw_location, withdraw_offset, left_banking, item_take, **common_args)
            clicker_common.break_action(rng, break_timer, break_time, break_prob, break_min, break_max)

            clicker_common.pause_action(rng, debug_mode)
            if not globvals.running:
                break

            clicker_common.close_interface(close_key, **common_args)
            clicker_common.break_action(rng, break_timer, break_time, break_prob, break_min, break_max)

            clicker_common.pause_action(rng, debug_mode)
            if not globvals.running:
                break

            clicker_common.open_spell_book(spell_book_key, **common_args)
            clicker_common.break_action(rng, break_timer, break_time, break_prob, break_min, break_max)

            clicker_common.pause_action(rng, debug_mode)
            if not globvals.running:
                break

            clicker_common.click_spell(spell_location, bank_location, **common_args)

            # At the end of the loop, print the status first right after last action
            # before rolling break dice to get status printed e.g. just before a very long break
            clicker_common.print_status(global_timer)

            clicker_common.break_action(rng, break_timer, break_time, break_prob, break_min, break_max)

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

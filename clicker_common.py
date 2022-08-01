import datetime
import os
import queue
import threading
import time

import pyautogui

import globvals
# noinspection PyRedeclaration
import quantumrandom_patched as quantumrandom


class Timer:
    def __init__(self):
        self._stamp: float = 0.0
        self.reset()

    # Resets the timer to present
    def reset(self) -> None:
        self._stamp = time.perf_counter()

    # Returns elapsed time floored to ms
    def elapsed(self) -> int:
        return int((time.perf_counter() - self._stamp) * 1000)


class Random:
    # Store class level constants
    # To have some reliable, tested defaults

    BITS: int = 56  # API: hex16 into BITS-bit unsigned integer

    ARRAY_SIZE: int = 10  # Values in total: DATA_COUNT * CHUNK_SIZE
    CHUNK_SIZE: int = 1024  # Hardcoded API Limit: 1024

    AUTOFILL_INTERVAL: float = 1.0  # How often to check whether needed to refill random data (to limit CPU usage)

    FETCH_TIMEOUT: float = 5.0  # How long to wait if no values are available, until error is thrown
    INSERT_TIMEOUT: float = 60.0  # How long to wait if queue is full
    ERROR_TIMEOUT: float = 10.0  # How long to wait if an error occurred during fetch until trying again

    MAX_ERROR_COUNT: int = 10  # How many times retry to fetch data from the API (failed due to connection error etc.)

    if BITS < 8 or BITS % 8 != 0:
        raise ValueError("BITS must be at least 8 and divisible by 8.")

    if not 0 < CHUNK_SIZE <= 1024:
        raise ValueError("CHUNK_SIZE must be between 1 and 1024.")

    if ARRAY_SIZE <= 0:
        raise ValueError("ARRAY_SIZE must be positive.")

    def __init__(self, count: int = None, size: int = None, autofill: bool = True, debug: bool = True):
        # Parameters for setting up
        self._debug: bool = debug
        self._array_size: int = count if count is not None else self.ARRAY_SIZE
        self._chunk_size: int = size if size is not None else self.CHUNK_SIZE

        if self._array_size <= 0:
            raise ValueError("array_size must be positive (>= 1).")
        if not 0 < self._chunk_size <= 1024:
            raise ValueError("size must be between 1 and 1024.")

        self._fail_count = 0
        self._fail_max = self.MAX_ERROR_COUNT

        self._max_size = self._array_size * self._chunk_size

        # Object for storing random data fetched from the API
        # Size is _chunk_size for all arrays plus one chunk extra space for filling
        self._data: queue.Queue = queue.Queue(self._max_size)

        if debug:
            print(f"Random: Queue initial status: {self._data.qsize()} / {self._max_size}")

        # Limit for int size, base of single random unit size in bits (decimal)
        self._limit: int = 2 ** self.BITS

        # For multithreading to prevent external access during critical operations
        self._running = True

        # Initialize the RNG when calling constructor
        self.__init()

        # Start autofill thread if autofill enabled
        if autofill:
            print("Autofill enabled.")
            self._fill_thread = threading.Thread(target=self.__fill_bg, name="autofill_bg_thread", daemon=True)
            self._fill_thread.start()
            if debug:
                print("Random: Fill thread started.")
        else:
            self._fill_thread = None
            print("Autofill disabled.")

    def __del__(self):
        # Ensure internal thread(s) are terminated before destructing the class
        self._running = False
        if self._fill_thread is not None and self._fill_thread.is_alive():
            print("Waiting for autofill thread to stop..")
            self._fill_thread.join(5)
            if self._debug:
                print("Random: fill thread joined.")
        if self._debug:
            print("Random: __del__ finished.")

    def __fill_bg(self):
        while self._running:
            time.sleep(self.AUTOFILL_INTERVAL)
            if self._running and self._data.qsize() < self._chunk_size:
                print("Random data at critical level. Fetch more data.")
                if self._debug:
                    print(f"Random: DATA STATUS: {self._data.qsize()} / {self._max_size}")
                # Fetch as much data than it roughly fits in the queue at the moment
                if self._array_size > 1:
                    self.__generate(self._max_size - self._chunk_size)
                else:
                    self.__generate(self._chunk_size)
        print("Autofill thread terminated.")

    def __generate(self, limit):
        """
        Fills the data until the given limit.
        The limit should be calculated based on the current number of values left compared to the max size.
        :param limit:
        :return:
        """
        if self._debug:
            print("Random: Generate data..")
            print(f"Random: LIMIT: {limit}")
            print(f"Random: DATA STATUS: {self._data.qsize()} / {self._max_size}")
        # If queue size is limit - 1 or less (at least block + 1 space available)
        while self._data.qsize() < limit:
            # GET CHUNK_SIZE number of BITS-bit unsigned integers
            # One full chunk at a time for maximum efficiency
            try:
                data = [int(h, 16) for h in quantumrandom.get_data('hex16', self._chunk_size, int(self.BITS / 8))]
                # Reset fail counter on fetch success
                self._fail_count = 0
            except Exception as ex:
                self._fail_count += 1
                print(f"Random: ERROR: Failed to fetch random data. Try {self._fail_count} of {self._fail_max}.")
                if self._fail_count >= self._fail_max:
                    print("Random: FATAL: FETCH FAIL TRIES LIMIT EXCEEDED!")
                    raise ex
                # If tries still left, wait for timeout and try again
                print(f"Random: Wait for {self.ERROR_TIMEOUT} secs before retrying..")
                time.sleep(self.ERROR_TIMEOUT)
                continue

            # After fetching full block, start inserting the values into the queue
            # For each iteration, ensure we are still running
            # To minimize unresponsive time
            for val in data:
                if self._running:
                    self._data.put(val, block=True, timeout=self.INSERT_TIMEOUT)

    def __init(self) -> None:
        """
        (Re)initializes the rng with fresh values.
        Can be called to ensure enough random values are buffered.
        CAUTION! Most expensive method, use only when necessary.
        :return:
        """
        print("Initializing RNG..")

        if self._debug:
            print(f"Random: BEFORE init: DATA STATUS {self._data.qsize()} / {self._max_size}")

        # Initialize only one chunk at startup to optimize for speed
        # More data will be generated on background during runtime
        if self._debug:
            print(f"Init fill size: {self._chunk_size}")

        self.__generate(self._chunk_size)

        if self._debug:
            print(f"Random: AFTER init: DATA STATUS {self._data.qsize()} / {self._max_size}")

        print("Initializing RNG done.")

    def __get_value(self) -> int:
        # Block until new values are received, or timeout is reached
        return self._data.get(block=True, timeout=self.FETCH_TIMEOUT)

    def random(self) -> float:
        """
        Returns a random float value in range [0, 1)
        Uniformly distributed between [0, BIT_COUNT - 1]
        :return:
        """
        # Since we are dealing with int16 (16 bits integer)
        # To get a value between 0..1 we need to break down the random value into 2^16 pieces
        # Then return the percentual value of the current number (to distribute value uniformly)
        # Source alue range eg.: 1 / 2**16 = 0.0000152587890625 per single random value
        return self.__get_value() / self._limit

    def randint(self, lo: int, hi: int) -> int:
        """
        Returns a random integer between a given range, [lo, hi]
        Uniformly distributed
        :param lo:
        :param hi:
        :return:
        """
        dist = hi - lo

        # First check that if the range is valid
        if dist < 0:
            raise ValueError("Max cannot be less than Min")
        # If lo == hi => return lo/hi
        if dist == 0:
            return lo

        # Limit the range to the maximum precision of 2^16
        # if rng > self._limit:
        #     raise ValueError(f"Distance between min and max cannot be over {self._limit}")

        return round(self.random() * dist) + lo


def _get_timestamp(local: bool, sep: str = ' ') -> str:
    if local:
        tm = datetime.datetime.now()
    else:
        tm = datetime.datetime.utcnow()
    return tm.isoformat(sep, 'seconds')


def read_settings(filename: str) -> dict[str, str]:
    try:
        file = open(filename, "r")
    except IOError as exc:
        print(f"ERROR: Failed to read settings file ({filename}). Ensure it exists in the current directory.")
        raise exc

    # Return settings as dict<str, str>
    data = {}
    for line in file:
        line = line.strip()
        if line == "" or line[0] == "#":
            continue
        values = line.split("=")
        data[str(values[0]).strip()] = str(values[1]).strip()

    file.close()
    return data


def read_inventory(filename: str):
    try:
        file = open(filename, "r", encoding="utf-8")
    except IOError as exc:
        print(f"ERROR: Failed to read item file ({filename}). Ensure it exists in the current directory.")
        raise exc

    data = []
    for line in file:
        line = line.strip()
        if line == "" or line[0] == "#":
            continue
        values = line.split(";")
        data.append([int(values[0].strip()), int(values[1].strip()), int(values[2].strip())])

    file.close()
    return data


def save_inventory(filename: str, items: list) -> None:
    try:
        file = open(filename, "a", encoding="utf-8")
    except IOError as ex:
        print(
            f"ERROR: Failed to write into item file ({filename}). Ensure this executable and the current user has "
            f"write permissions on this directory.")
        print(f"Exception details: {ex}")
        raise ex

    # Get ISO timestamp in local TZ
    stamp: str = _get_timestamp(local=True)

    # First, append header to separate from previous runs
    file.write(f"{os.linesep}### ITEMS SAVED ON {stamp} ###{os.linesep}")

    # Then, append items with their curent status
    for it in items:
        file.write(str(it[0]) + ";" + str(it[1]) + ";" + str(it[2]))
        file.write(os.linesep)

    # Write the footer to separate from other runs
    file.write(f"### END OF ITEMS ON {stamp}{os.linesep}")

    file.close()


def init_rng() -> any:
    rng = Random(debug=False)
    return rng


def rand_sleep(min_ms: int, max_ms: int, **kwargs) -> float:
    # Read common parameters from packed kwargs
    rng: any = kwargs['rng']
    debug: bool = kwargs['debug']

    if min_ms > max_ms:
        raise ValueError("Min must be less than max.")
    if min_ms == max_ms:
        tm = min_ms
    else:
        tm = rng.randint(min_ms, max_ms)
    if debug:
        print(f"Delay for: {tm} ms")
    time.sleep(tm / 1000)
    return tm


def _rand_mouse_speed(min_ms: int, max_ms: int, **kwargs) -> float:
    # Read common parameters from packed kwargs
    rng: any = kwargs['rng']
    debug: bool = kwargs['debug']

    if min_ms > max_ms:
        raise ValueError("Min must be less than max.")
    tm = rng.randint(min_ms, max_ms)
    if debug:
        print(f"Mouse speed: {tm} ms")
    return tm / 1000


def _randomized_offset(location: tuple[int, int], **kwargs) -> tuple[int, int]:
    # Read common parameters from packed kwargs
    rng: any = kwargs['rng']
    max_off: int = kwargs['max_off']
    window_name: str = kwargs['window_name']
    debug: bool = kwargs['debug']

    w = window(window_name).topleft if window_name is not None else None

    ox = w.x + location[0] if w is not None else location[0]
    oy = w.y + location[1] if w is not None else location[1]

    nx = rng.randint(ox - max_off, ox + max_off)
    ny = rng.randint(oy - max_off, oy + max_off)

    if debug:
        print(f"Original Target: X: {ox} Y: {oy}")
        print(f"New Target: X: {nx}, Y: {ny}")

    return nx, ny


def _mouse_movement_background(move_min: int, move_max: int, **kwargs) -> None:
    print("Mouse movement BG Thread started.")

    # Read common parameters from packed kwargs
    rng: any = kwargs['rng']

    while globvals.running:
        rand_sleep(50, 1000, **kwargs)

        if not globvals.running:
            break

        # Skip loop only after the delay to not loop too fast in case can_move=False
        if not globvals.can_move:
            continue

        for i in range(0, rng.randint(0, 10)):
            rand_sleep(10, 100, **kwargs)
            if not globvals.running or not globvals.can_move:
                break
            x, y = _randomized_offset(
                (rng.randint(move_min, move_max), rng.randint(move_min, move_max)),
                **{**kwargs, 'window_name': None})
            pyautogui.moveRel(x, y, _rand_mouse_speed(30, 80, **kwargs))

    print("Mouse movement BG Thread terminated.")


def init_movement_thread(rand_min: int, rand_max: int, **kwargs) -> threading.Thread:
    return threading.Thread(
        target=_mouse_movement_background,
        name="bg_mouse_movement",
        args=(rand_min, rand_max),
        kwargs=kwargs
        # daemon=True
    )


def window(name: str) -> any:
    try:
        return pyautogui.getWindowsWithTitle(name)[0]
    except IndexError:
        print("ERROR: Game client window was not detected. Ensure the game client is running first.")
        print("Also check that window title is correct in settings.")
        raise RuntimeError("Could not detect game window.")


def print_start_info(key: int) -> None:
    print(f"Started. Hit key with code {key} at any time to stop execution.")
    print("NOTE: Ensure settings are correctly defined in settings file.")
    print("NOTE: Ensure item details are correctly set in items data file (if applicable).")
    print("NOTE: Please do not move the mouse anymore since the program has been started.")


def start_delay(rng: any) -> None:
    print("Waiting 5 seconds before starting to action...")
    rand_sleep(5000, 5000, rng=rng, debug=True)  # debug=True


def print_status(timer: Timer) -> None:
    seconds = timer.elapsed() / 1000
    hours = int(seconds / 3600)
    minutes = int(seconds / 60 - hours * 60)
    seconds = int(seconds - hours * 3600 - minutes * 60)

    print(f"Total elapsed: {hours} h | {minutes} min | {seconds} sec.")
    print(f"Timestamp: {_get_timestamp(local=True)}")


# Catches key interrupt events
# Gracefully terminates the program
def interrupt_handler(event) -> None:
    print("Program interrupted.")
    globvals.running = False
    print("Possibly still waiting for a sleep to finish..")


# Catches pause key presses
# Pauses the program until resumed
def pause_handler(event) -> None:
    if not globvals.paused:
        print("Program paused.")
        # can_move does not globally change from here!
        # must be changed at the script global level
        # globvals.can_move = False
        globvals.paused = True
    else:
        print("Program resumed.")
        # can_move does not globally change from here!
        # must be changed at the script global level
        # globvals.can_move = True
        globvals.paused = False
    print("Possibly still waiting for a sleep to finish..")


def exit_handler() -> None:
    input("Press ENTER to EXIT...")


def _hover_raw(x: int, y: int, **kwargs) -> None:
    # Read common parameters from packed kwargs
    speed_min: int = kwargs['speed_min']
    speed_max: int = kwargs['speed_max']
    debug: bool = kwargs['debug']

    if debug:
        print(f"Hover target: ({x}, {y})")
    pyautogui.moveTo(x, y, _rand_mouse_speed(speed_min, speed_max, **kwargs))


def _left_click_raw(x: int, y: int, **kwargs) -> None:
    # Read common parameters from packed kwargs
    speed_min: int = kwargs['speed_min']
    speed_max: int = kwargs['speed_max']
    debug: bool = kwargs['debug']

    if debug:
        print(f"Left Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits the target correctly
    globvals.can_move = False
    pyautogui.moveTo(x, y, _rand_mouse_speed(speed_min, speed_max, **kwargs))
    pyautogui.leftClick()
    globvals.can_move = True


def _right_click_raw(x: int, y: int, **kwargs) -> None:
    # Read common parameters from packed kwargs
    speed_min: int = kwargs['speed_min']
    speed_max: int = kwargs['speed_max']
    debug: bool = kwargs['debug']

    if debug:
        print(f"Right Click target: ({x}, {y})")

    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    globvals.can_move = False
    pyautogui.moveTo(x, y, _rand_mouse_speed(speed_min, speed_max, **kwargs))
    pyautogui.rightClick()
    globvals.can_move = True


def _key_press_raw(key: str, **kwargs):
    # Read common parameters from packed kwargs
    debug: bool = kwargs['debug']

    if debug:
        print(f"Press Key: {key}")
    pyautogui.press(key, presses=1)


def _take_break(break_min, break_max, **kwargs) -> None:
    print("Taking a break.")
    rand_sleep(break_min, break_max, **{**kwargs, 'debug': True})  # Longer break -> always debug print output


def key_press(key: str, **kwargs) -> None:
    # Read common parameters from packed kwargs
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']

    rand_sleep(action_min, action_max, **kwargs)
    _key_press_raw(key, **kwargs)


def hover(location: tuple[int, int], **kwargs) -> None:
    # Read common parameters from packed kwargs
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']

    # Wait for a while before next action
    rand_sleep(action_min, action_max, **kwargs)

    # Calculate randomized-off x,y and hover to the target first
    x, y = _randomized_offset(location, **kwargs)
    _hover_raw(x, y, **kwargs)


def hover_click(location: tuple[int, int], **kwargs) -> None:
    # Read common parameters from packed kwargs
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']

    # Calculate randomized-off x,y and hover to the target first
    x, y = _randomized_offset(location, **kwargs)
    _hover_raw(x, y, **kwargs)

    # Wait for a while before next action
    rand_sleep(action_min, action_max, **kwargs)

    # Recalculate random-off x,y and click the target
    x, y = _randomized_offset(location, **kwargs)
    _left_click_raw(x, y, **kwargs)


def hover_context_click(location: tuple[int, int], offset: int, **kwargs) -> None:
    # Read common parameters from packed kwargs
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']

    # Calculate randomized-off x,y and hover to the target first
    x, y = _randomized_offset(location, **kwargs)
    _hover_raw(x, y, **kwargs)

    # Wait for a while before next action
    rand_sleep(action_min, action_max, **kwargs)

    # Right click the target to open context menu
    x, y = _randomized_offset(location, **kwargs)
    _right_click_raw(x, y, **kwargs)

    # Hover to the context menu offset
    x, y = _randomized_offset((location[0], location[1] + offset), **{**kwargs, 'max_off': 1})
    _hover_raw(x, y, **kwargs)

    # Wait a bit before proceeding
    rand_sleep(action_min, action_max, **kwargs)

    # Finally, click the menu option in the predefined offset
    x, y = _randomized_offset(location, **{**kwargs, 'max_off': 2})
    _left_click_raw(x, y, **kwargs)


def focus_window(**kwargs) -> None:
    # Read common parameters from packed kwargs
    rng: any = kwargs['rng']

    print("Focus on game window.")
    # Set max_off to 0 to for max accuracy
    hover_click((rng.randint(50, 900), rng.randint(10, 40)), **{**kwargs, 'max_off': 0})


def close_interface(key: str, **kwargs) -> None:
    # Read common parameters from packed kwargs
    close_min: int = kwargs['close_min']
    close_max: int = kwargs['close_max']

    print("Close current interface.")
    rand_sleep(close_min, close_max, **kwargs)
    key_press(key, **kwargs)


def open_location(location: tuple[int, int], **kwargs) -> None:
    print("Open location.")
    hover_click(location, **kwargs)


def open_menu(key: str, **kwargs) -> None:
    print("Ensure menu open.")
    key_press(key, **kwargs)


def withdraw_item(location: tuple[int, int], offset: int, left_banking: bool, item_take: int, **kwargs) -> None:
    debug: bool = kwargs['debug']

    print("Withdraw item.")

    if debug:
        print(f"Item subtraction: {globvals.item_left} - {item_take}")

    # Throws Error if item_left not set by script
    if globvals.item_left < item_take:
        print("Out of item(s)! Stopping and exiting..")
        globvals.running = False
        return

    globvals.item_left -= item_take

    if left_banking:
        print("Using left click method.")
        hover_click(location, **kwargs)
    else:
        print("Using context menu method.")
        hover_context_click(location, offset, **kwargs)


def deposit_item(location: tuple[int, int], offset: int, left_banking: bool, **kwargs) -> None:
    print("Deposit item.")

    if left_banking:
        print("Deposit using left click.")
        hover_click(location, **kwargs)
    else:
        print("Deposit using right click context menu.")
        hover_context_click(location, offset, **kwargs)


def withdraw_items(
        first_location: tuple[int, int],
        first_offset: int,
        item_take: int,
        second_location: tuple[int, int],
        second_offset: int,
        item2_take: int,
        left_banking: bool,
        **kwargs
) -> None:
    # Read common parameters from packed kwargs
    debug: bool = kwargs['debug']

    print("Withdraw items.")

    if debug:
        print(f"Item subtraction: {globvals.item_left} - {item_take}")
        print(f"Item2 subtraction: {globvals.item2_left} - {item2_take}")

    # Throws Error if item_left not set by script
    if globvals.item_left < item_take or globvals.item2_left < item2_take:
        print("Out of item(s)! Stopping and exiting..")
        globvals.running = False
        return

    globvals.item_left -= item_take
    globvals.item2_left -= item2_take

    if left_banking:
        hover_click(first_location, **kwargs)
        hover_click(second_location, **kwargs)
    else:
        hover_context_click(first_location, first_offset, **kwargs)
        hover_context_click(second_location, second_offset, **kwargs)


def deposit_items(
        first_location: tuple[int, int],
        first_offset: int,
        second_location: tuple[int, int],
        second_offset: int,
        left_banking: bool,
        **kwargs
) -> None:
    print("Deposit items.")

    if left_banking:
        hover_click(first_location, **kwargs)
        hover_click(second_location, **kwargs)
    else:
        hover_context_click(first_location, first_offset, **kwargs)
        hover_context_click(second_location, second_offset, **kwargs)


def combine_items(first_location: tuple[int, int], second_location: tuple[int, int], **kwargs) -> None:
    print("Combine items.")
    hover_click(first_location, **kwargs)
    hover_click(second_location, **kwargs)


def click_spell(spell_location: tuple[int, int], bank_location: tuple[int: int], **kwargs) -> None:
    print("Click spell.")
    hover_click(spell_location, **kwargs)

    if bank_location is not None:
        print("Already hover on bank right after.")
        hover(bank_location, **kwargs)


def confirm_action(key: str, next_location: tuple[int, int] = None, **kwargs):
    # Read common parameters from packed kwargs
    close_min: int = kwargs['close_min']
    close_max: int = kwargs['close_max']

    print("Confirm action.")
    rand_sleep(close_min, close_max, **kwargs)
    key_press(key, **kwargs)

    # Immediately hover mouse over bank after started action
    if next_location is not None:
        hover(next_location, **kwargs)


def break_action(break_min: int, break_max: int, break_time: int, break_prob: float, break_timer: Timer,
                 **kwargs) -> None:
    # Read common parameters from packed kwargs
    rng: any = kwargs['rng']

    # If enough time from previous break passed, and random number hits prob
    if break_timer.elapsed() >= break_time and rng.random() < break_prob:
        break_timer.reset()
        globvals.can_move = False
        _take_break(break_min, break_max, **kwargs)
        globvals.can_move = True


def pause_action(**kwargs) -> None:
    # Disable random movement during pause
    globvals.can_move = False
    while globvals.paused:
        if not globvals.running:
            break
        # Only sleep 1 sec per loop to minimize response delay
        rand_sleep(1000, 1000, **kwargs)
    globvals.can_move = True

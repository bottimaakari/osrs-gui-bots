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


def get_timestamp(local: bool, sep: str = ' ') -> str:
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
    stamp: str = get_timestamp(local=True)

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


def rand_sleep(rng: any, min_ms: int, max_ms: int, debug: bool = True):
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


def rand_mouse_speed(rng: any, min_ms: int, max_ms: int, debug: bool = True) -> float:
    if min_ms > max_ms:
        raise ValueError("Min must be less than max.")
    tm = rng.randint(min_ms, max_ms)
    if debug:
        print(f"Mouse speed: {tm} ms")
    return tm / 1000


def randomized_offset(rng: any, x: int, y: int, max_off: int, window_title: str = None, debug: bool = True) \
        -> tuple[int, int]:
    w = window(window_title).topleft if window_title is not None else None

    ox = w.x + x if w is not None else x
    oy = w.y + y if w is not None else y

    nx = rng.randint(ox - max_off, ox + max_off)
    ny = rng.randint(oy - max_off, oy + max_off)

    if debug:
        print(f"Original Target: X: {x} Y: {y}")
        print(f"New Target: X: {nx}, Y: {ny}")

    return nx, ny


def mouse_movement_background(rng: any, move_min: int, move_max: int, max_off: int, debug: bool = True) -> None:
    print("Mouse movement BG Thread started.")

    while globvals.running:
        rand_sleep(rng, 50, 1000, debug)

        if not globvals.running:
            break

        # Skip loop only after the delay to not loop too fast in case can_move=False
        if not globvals.can_move:
            continue

        for i in range(0, rng.randint(0, 10)):
            rand_sleep(rng, 10, 100, debug)
            if not globvals.running or not globvals.can_move:
                break
            x, y = randomized_offset(rng,
                                     rng.randint(move_min, move_max),
                                     rng.randint(move_min, move_max),
                                     max_off,
                                     debug=debug
                                     )
            pyautogui.moveRel(x, y, rand_mouse_speed(rng, 30, 80, debug))

    print("Mouse movement BG Thread terminated.")


def create_movement_thread(
        rand_min: int,
        rand_max: int,
        **kwargs
) -> threading.Thread:
    rng: any = kwargs['rng']
    max_off: int = kwargs['max_off']
    debug: bool = kwargs['debug']

    return threading.Thread(
        target=mouse_movement_background,
        name="bg_mouse_movement",
        args=(rng, rand_min, rand_max, max_off, debug),
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
    rand_sleep(rng, 5000, 5000)  # debug=True


def print_status(timer: Timer) -> None:
    seconds = timer.elapsed() / 1000
    hours = int(seconds / 3600)
    minutes = int(seconds / 60 - hours * 60)
    seconds = int(seconds - hours * 3600 - minutes * 60)

    print(f"Total elapsed: {hours} h | {minutes} min | {seconds} sec.")
    print(f"Timestamp: {get_timestamp(local=True)}")


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


def hover_raw(rng: any, x: int, y: int, speed_min: int, speed_max: int, debug: bool = True):
    if debug:
        print(f"Hover target: ({x}, {y})")
    pyautogui.moveTo(x, y, rand_mouse_speed(rng, speed_min, speed_max, debug))


def left_click_raw(rng: any, x: int, y: int, speed_min: int, speed_max: int, debug: bool = True):
    if debug:
        print(f"Left Click target: ({x}, {y})")
    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    globvals.can_move = False
    pyautogui.moveTo(x, y, rand_mouse_speed(rng, speed_min, speed_max, debug))
    pyautogui.leftClick()
    globvals.can_move = True


def right_click_raw(rng: any, x: int, y: int, speed_min: int, speed_max: int, debug: bool = True):
    if debug:
        print(f"Right Click target: ({x}, {y})")
    # Temporarily prevent background movement
    # to ensure the click hits target correctly
    globvals.can_move = False
    pyautogui.moveTo(x, y, rand_mouse_speed(rng, speed_min, speed_max, debug))
    pyautogui.rightClick()
    globvals.can_move = True


def key_press_raw(key: str, debug: bool = True):
    if debug:
        print(f"Press Key: {key}")
    pyautogui.press(key, presses=1)


def key_press(
        rng: any,
        key: str,
        action_min: int,
        action_max: int,
        debug: bool = True
) -> None:
    rand_sleep(rng, action_min, action_max, debug)
    key_press_raw(key, debug)


def hover(
        rng: any,
        location: tuple[int, int],
        max_off: int,
        action_min: int,
        action_max: int,
        speed_min: int,
        speed_max: int,
        window_name: str,
        debug: bool = True
) -> None:
    # Wait for a while before next action
    rand_sleep(rng, action_min, action_max, debug)

    # Calculate randomized-off x,y and hover to the target first
    x, y = randomized_offset(rng, location[0], location[1], max_off, window_name, debug)
    hover_raw(rng, x, y, speed_min, speed_max, debug)


def hover_click(
        rng: any,
        location: tuple[int, int],
        max_off: int,
        action_min: int,
        action_max: int,
        speed_min: int,
        speed_max: int,
        window_name: str,
        debug: bool = True
) -> None:
    # Calculate randomized-off x,y and hover to the target first
    x, y = randomized_offset(rng, location[0], location[1], max_off, window_name, debug)
    hover_raw(rng, x, y, speed_min, speed_max, debug)

    # Wait for a while before next action
    rand_sleep(rng, action_min, action_max, debug)

    # Recalculate random-off x,y and click the target
    x, y = randomized_offset(rng, location[0], location[1], max_off, window_name, debug)
    left_click_raw(rng, x, y, speed_min, speed_max, debug)


def hover_context_click(
        rng: any,
        location: tuple[int, int],
        offset: int,
        max_off: int,
        action_min: int,
        action_max: int,
        speed_min: int,
        speed_max: int,
        window_name: str,
        debug: bool = True
) -> None:
    # Calculate randomized-off x,y and hover to the target first
    x, y = randomized_offset(rng, location[0], location[1], max_off, window_name, debug)
    hover_raw(rng, x, y, speed_min, speed_max, debug)

    # Wait for a while before next action
    rand_sleep(rng, action_min, action_max, debug)

    # Right click the target to open context menu
    x, y = randomized_offset(rng, location[0], location[1], max_off, window_name, debug)
    right_click_raw(rng, x, y, speed_min, speed_max, debug)

    # Hover to the context menu offset
    x, y = randomized_offset(rng, location[0], location[1] + offset, 1, window_name, debug)
    hover_raw(rng, x, y, speed_min, speed_max, debug)

    # Wait a bit before proceeding
    rand_sleep(rng, action_min, action_max, debug)

    # Finally, click the menu option in the predefined offset
    x, y = randomized_offset(rng, location[0], location[1] + offset, 1, window_name, debug)
    left_click_raw(rng, x, y, speed_min, speed_max, debug)


def take_break(rng, break_min, break_max) -> None:
    print("Taking a break.")
    rand_sleep(rng, break_min, break_max)  # Longer break -> always debug print output


def focus_window(
        debug: bool = True,
        **kwargs
) -> None:
    # Read generic parameters from packaged kwargs
    rng: any = kwargs['rng']
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']
    speed_min: int = kwargs['speed_min']
    speed_max: int = kwargs['speed_max']
    window_name: str = kwargs['window_name']

    print("Focus on game window.")
    hover_click(rng, (100, 5), 0, action_min, action_max, speed_min, speed_max, window_name, debug)


def open_bank(
        bank_location: tuple[int, int],
        **kwargs
) -> None:
    # Read generic parameters from packaged kwargs
    rng: any = kwargs['rng']
    max_off: int = kwargs['max_off']
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']
    speed_min: int = kwargs['speed_min']
    speed_max: int = kwargs['speed_max']
    window_name: str = kwargs['window_name']
    debug: bool = kwargs['debug']

    print("Open bank.")
    hover_click(rng, bank_location, max_off, action_min, action_max, speed_min, speed_max, window_name, debug)


def withdraw_item(
        location: tuple[int, int],
        offset: int,
        left_banking: bool,
        item_take: int,
        **kwargs
) -> None:
    # Read generic parameters from packaged kwargs
    rng: any = kwargs['rng']
    max_off: int = kwargs['max_off']
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']
    speed_min: int = kwargs['speed_min']
    speed_max: int = kwargs['speed_max']
    window_name: str = kwargs['window_name']
    debug: bool = kwargs['debug']

    print("Withdraw item(s).")

    if debug:
        print(f"Item subtraction: {globvals.item_left} - {item_take}")

    if globvals.item_left < item_take:
        print("Out of item(s)! Stopping and exiting..")
        globvals.running = False
        return

    globvals.item_left -= item_take

    if left_banking:
        print("Using left click method.")
        hover_click(rng, location, max_off, action_min, action_max, speed_min, speed_max, window_name, debug)
    else:
        print("Using context menu method.")
        hover_context_click(rng, location, offset, max_off, action_min, action_max, speed_min,
                            speed_max, window_name, debug)


def deposit_item(
        location: tuple[int, int],
        offset: int,
        left_banking: bool,
        **kwargs
) -> None:
    # Read generic parameters from packaged kwargs
    rng: any = kwargs['rng']
    max_off: int = kwargs['max_off']
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']
    speed_min: int = kwargs['speed_min']
    speed_max: int = kwargs['speed_max']
    window_name: str = kwargs['window_name']
    debug: bool = kwargs['debug']

    print("Deposit item(s).")

    if left_banking:
        print("Deposit using left click.")
        hover_click(rng, location, max_off, action_min, action_max, speed_min, speed_max, window_name, debug)
    else:
        print("Deposit using right click context menu.")
        hover_context_click(rng, location, offset, max_off, action_min, action_max, speed_min,
                            speed_max, window_name, debug)


def close_interface(
        key: str,
        **kwargs
) -> None:
    # Read generic parameters from packaged kwargs
    rng: any = kwargs['rng']
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']
    close_min: int = kwargs['close_min']
    close_max: int = kwargs['close_max']
    debug: bool = kwargs['debug']

    print("Close current interface.")
    rand_sleep(rng, close_min, close_max, debug)
    key_press(rng, key, action_min, action_max, debug)


def open_spell_book(
        key: str,
        **kwargs
) -> None:
    # Read generic parameters from packaged kwargs
    rng: any = kwargs['rng']
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']
    debug: bool = kwargs['debug']

    print("Ensure spell book open.")
    key_press(rng, key, action_min, action_max, debug)


def click_spell(
        spell_location: tuple[int, int],
        bank_location: tuple[int: int],
        **kwargs
) -> None:
    # Read generic parameters from packaged kwargs
    rng: any = kwargs['rng']
    max_off: int = kwargs['max_off']
    action_min: int = kwargs['action_min']
    action_max: int = kwargs['action_max']
    speed_min: int = kwargs['speed_min']
    speed_max: int = kwargs['speed_max']
    window_name: str = kwargs['window_name']
    debug: bool = kwargs['debug']

    print("Click spell.")
    hover_click(rng, spell_location, max_off, action_min, action_max, speed_min, speed_max, window_name, debug)

    if bank_location is not None:
        print("Already hover on bank right after.")
        hover(rng, bank_location, max_off, action_min, action_max, speed_min, speed_max, window_name, debug)


def break_action(
        rng: any,
        break_timer: Timer,
        break_time: int,
        break_prob: float,
        break_min: int,
        break_max: int
) -> None:
    # If enough time from previous break passed, and random number hits prob
    if break_timer.elapsed() >= break_time and rng.random() < break_prob:
        break_timer.reset()
        globvals.can_move = False
        take_break(rng, break_min, break_max)
        globvals.can_move = True


def pause_action(
        rng: any,
        debug: bool = True
) -> None:
    # Disable random movement during pause
    globvals.can_move = False
    while globvals.paused:
        if not globvals.running:
            break
        # Only sleep 1 sec per loop to minimize response delay
        rand_sleep(rng, 1000, 1000, debug)
    globvals.can_move = True

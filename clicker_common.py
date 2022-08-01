import threading
import time
from typing import List

import pyautogui
import quantumrandom

import globvals


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
    CHUNK_SIZE: int = 1024  # API Limit: 1024
    VALUE_SIZE: int = 16  # API: int16 -> 16
    ARRAY_SIZE: int = 10  # Values in total: DATA_COUNT * CHUNK_SIZE
    AUTOFILL_INTEVAL: float = 1.0  # How often to check whether needed to refill random data
    AUTOFILL_THRESHOLD: int = 50  # Threshold when its time to refill the random data (nums left in the last list)

    def __init__(self, count: int = None, size: int = None, autofill: bool = True):
        # Parameters for setting up data
        self._array_size = count if count is not None else self.ARRAY_SIZE
        self._chunk_size = size if size is not None else self.CHUNK_SIZE

        # Object for storing random data fetched from the API
        self._data: List[List[int]] = []

        # Pointers foor iterating over the data object
        self._len_data: int = 0
        self._list_it: int = 0
        self._value_it: int = -1

        # Limit for int size, base of single random unit size in bits (decimal)
        self._limit: int = 2 ** self.VALUE_SIZE

        # For multithreading to prevent external access during critical operations
        self._initializing = False
        self._critical = False
        self._running = True

        # Initialize the RNG when calling constructor
        self.init()

        # Start autofill thread if autofill enabled
        if autofill:
            print("Autofill enabled.")
            self._fill_thread = threading.Thread(target=self.__fill_thread, name="autofill_bg_thread", daemon=True)
            self._fill_thread.start()
        else:
            self._fill_thread = None
            print("Autofill disabled.")

    def __fill_thread(self):
        while self._running:
            # print("Autofill loop.")
            time.sleep(self.AUTOFILL_INTEVAL)
            # When critical level reached (1 slot with 10% left)
            # if self._running and self._list_it >= self._len_data - 1 and self._value_it >= self._chunk_size * 0.1:
            if self._running and \
                    self._list_it >= self._len_data - 1 and \
                    self._value_it >= self._chunk_size - self.AUTOFILL_THRESHOLD - 1:
                print("Random data at critical level. Reinit data.")
                self.init()

        print("Autofill thread exiting.")

    def __get_value(self) -> int:
        # If initialization is in progress
        # Sleep until the initialization is done
        while self._critical:
            time.sleep(0.01)
        if self._value_it >= self._chunk_size - 1:
            self._list_it += 1
            self._value_it = -1
        self._value_it += 1
        return self._data[self._list_it][self._value_it]

    def __del__(self):
        # Ensure internal thread(s) are terminated before destructing the class
        self._running = False
        if self._fill_thread and self._fill_thread.is_alive():
            print("Waiting for autofill thread to stop..")
            self._fill_thread.join(5)

    def init(self) -> None:
        """
        (Re)initializes the rng with fresh values.
        Can be called to ensure enough random values are buffered.
        CAUTION! Most expensive method, use only when necessary
        :return:
        """
        # Ensure no one tries to init the same instance at the same time
        if self._initializing:
            print("Already initializing. No need to initialize this often.")
            return

        self._initializing = True
        print("Initializing RNG..")

        new_data: List[List[int]] = []

        for i in range(self._array_size):
            new_data.append(quantumrandom.get_data('uint16', self._chunk_size))

        # ENTER CRITICAL SECTION
        self._critical = True
        # Ensure nobody is in middle of fetching data etc.
        time.sleep(0.5)

        # Free the memory of old random data
        # and ensure its garbage collected
        self._data.clear()
        del self._data
        self._data = new_data

        # (Re)Define len data as constant for later use
        # Reset list pointers
        self._len_data = len(self._data)
        self._list_it = 0
        self._value_it = -1

        # Sanity check -> does the generated data match any close what was requested
        # If not - a programming error exists
        if self._len_data != self._array_size or len(self._data[self._len_data - 1]) != self._chunk_size:
            raise Exception("Failed to initialize RNG: Data count mismatch!")

        self._critical = False
        # EXIT CRITICAL SECTION

        print("Initializing RNG done.")
        self._initializing = False

    def random(self) -> float:
        """
        Returns a random float value in range [0, 1)
        Uniformly distributed between [0, BIT_COUNT - 1]
        :return:
        """
        # Since we are dealing with int16 (16 bits integer)
        # To get a value between 0..1 we need to break down the random value into 2^16 pieces
        # Then return the percentual value of the current number (to distribute value uniformly)
        # Entropy is: 1 / 2**16 = 0.0000152587890625 per single random value
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

        # Limit the range to the maximum precision of 2^16
        # if rng > self._limit:
        #     raise ValueError(f"Distance between min and max cannot be over {self._limit}")

        return round(self.random() * dist) + lo


def read_settings(filename: str):
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


def save_inventory(filename: str, items: list):
    try:
        file = open(filename, "r", encoding="utf-8")
    except IOError as ex:
        print(
            f"ERROR: Failed to write into item file ({filename}). Ensure this executable and the current user has "
            f"write permissions on this directory.")
        print(f"Exception details: {ex}")
        raise ex

    for it in items:
        file.write(str(it[0]) + ";" + str(it[1]) + ";" + str(it[2]))
        file.write("\r\n")  # TODO CRLF on win, LF on *nix

    file.close()


def init_rng():
    rng = Random()
    return rng


def rand_sleep(rng, minms: int, maxms: int, debug: bool = True):
    if minms > maxms:
        raise ValueError("Min must be less than max.")
    tm = rng.randint(minms, maxms)
    if debug:
        print(f"Delay for: {tm} ms")
    time.sleep(tm / 1000)
    return tm


def rand_mouse_speed(rng, minms: int, maxms: int, debug: bool = True):
    if minms > maxms:
        raise ValueError("Min must be less than max.")
    tm = rng.randint(minms, maxms)
    if debug:
        print(f"Mouse speed: {tm} ms")
    return tm / 1000


def randomized_offset(rng, x: int, y: int, max_off: int, window_title: str = None, debug: bool = True):
    w = window(window_title).topleft if window_title is not None else None

    ox = w.x + x if w is not None else x
    oy = w.y + y if w is not None else y

    nx = rng.randint(ox - max_off, ox + max_off)
    ny = rng.randint(oy - max_off, oy + max_off)

    if debug:
        print(f"Target: X: {nx}, Y: {ny}")

    return nx, ny


def mouse_movement_background(rng, move_min: int, move_max: int, max_off: int, debug: bool = True):
    print("Mouse movement BG Thread started.")

    while globvals.running:
        rand_sleep(rng, 50, 1000, debug)

        if not globvals.running:
            break

        # Skip loop only after the delay to not loop too fast in case can_move=False
        if not globvals.can_move:
            continue

        for i in range(0, rng.randint(0, rng.randint(0, 10))):
            rand_sleep(rng, 20, 50, debug)
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


def window(name):
    return pyautogui.getWindowsWithTitle(name)[0]


def print_info(key):
    print(f"Started. Hit key with code {key} at any time to stop execution.")
    print("NOTE: Ensure settings are correctly defined in settings file.")
    print("NOTE: Ensure item details are correctly set in items data file (if applicable).")
    print("NOTE: Please do not move the mouse anymore since the program has been started.")


def start_delay(rng):
    print("Waiting 4 seconds before starting..")
    rand_sleep(rng, 4000, 4000)  # debug=True


def print_status(timer: Timer):
    secs = timer.elapsed() / 1000
    hrs = int(secs / 3600)
    mins = int(secs / 60 - hrs * 60)
    secs = int(secs - hrs * 3600 - mins * 60)
    print(f"Total elapsed: {hrs} hrs | {mins} mins | {secs} secs.")
    print(f"Timestamp: {datetime.datetime.now()}")

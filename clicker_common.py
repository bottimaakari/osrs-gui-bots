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
    CHUNK_SIZE: int = 1024  # API Limit: 1024
    VALUE_SIZE: int = 16  # API: int16 -> 16
    DATA_COUNT: int = 30  # Values in total: DATA_COUNT * DATA_SIZE

    def __init__(self, count: int = None, size: int = None):
        self._data_count = count if count is not None else self.DATA_COUNT
        self._data_size = size if size is not None else self.CHUNK_SIZE
        self._data: List[List[int]] = []
        self._len_data: int = 0
        self._list_it: int = 0
        self._value_it: int = -1
        self._limit: int = 2 ** self.VALUE_SIZE
        self._call_count = 0
        self.init()

    def __get_value(self) -> int:
        self._call_count += 1
        if self._value_it >= self._data_size - 1:
            self._list_it += 1
            self._value_it = -1
        self._value_it += 1
        return self._data[self._list_it][self._value_it]

    def init(self) -> None:
        """
        (Re)initializes the rng with fresh values.
        Can be called to ensure enough random values are buffered.
        CAUTION! Most expensive method, use only when necessary
        :return:
        """
        print("Initializing RNG..")

        self._data.clear()

        for i in range(self._data_count):
            self._data.append(quantumrandom.get_data('uint16', self._data_size))

        # Define len data as constant for later use
        # Reset list pointers
        self._len_data = len(self._data)
        self._list_it = 0
        self._value_it = -1

        # Sanity check -> does the generated data match anyclose what was requested
        if self._len_data < self._data_count or len(self._data[self._len_data - 1]) < self._data_size:
            raise Exception("Failed to initialize RNG: Data count mismatch!")

        print("Initializing RNG done.")

    def random(self) -> float:
        """
        Returns a random float value in range [0, 1)
        Uniformly distributed between [0, BIT_COUNT - 1]
        :return:
        """
        # Since we are dealing with int16 (16 bits integer)
        # To get a value between 0..1 we need to break down the random value into 2^16 pieces
        # Then return the percentual value of the current number (to distribute value uniformly)
        return self.__get_value() / self._limit

    def randint(self, lo: int, hi: int) -> int:
        """
        Returns a random integer between a given range, [lo, hi]
        Uniformly distributed
        :param lo:
        :param hi:
        :return:
        """
        rng = hi - lo

        # First check that if the range is valid
        if rng < 0:
            raise ValueError("Max cannot be less than Min")

        # Limit the range to the maximum precision of 2^16
        if rng > self._limit:
            raise ValueError(f"Distance between min and max cannot be over {self._limit}")

        return round(self.random() * rng) + lo


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
    pyautogui.sleep(tm / 1000)
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
        rand_sleep(rng, 10, 1000, debug)

        if not globvals.running:
            break

        # Skip loop only after the delay to not loop too fast in case can_move=False
        if not globvals.can_move:
            continue

        for i in range(0, rng.randint(0, rng.randint(0, 8))):
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

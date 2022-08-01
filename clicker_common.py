import secrets
import time

import pyautogui


class Timer:
    _stamp = None

    def __init__(self):
        self.reset()

    # Resets the timer to present
    def reset(self):
        self._stamp = time.perf_counter()

    # Returns elapsed time floored to ms
    def elapsed(self) -> int:
        return int((time.perf_counter() - self._stamp) * 1000)


def read_settings(filename):
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


def read_inventory(filename):
    try:
        file = open(filename, "r")
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


def save_inventory(filename, items: list):
    file = None

    try:
        file = open(filename, "r")
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


def rand_sleep(rng, minms, maxms, debug=True):
    if minms > maxms:
        raise ValueError("Min must be less than max.")
    tm = rng.randint(minms, maxms)
    if debug:
        print(f"Delay for: {tm} ms")
    pyautogui.sleep(tm / 1000)
    return tm


def rand_mouse_speed(rng, minms, maxms, debug=True):
    if minms > maxms:
        raise ValueError("Min must be less than max.")
    tm = rng.randint(minms, maxms)
    if debug:
        print(f"Mouse speed: {tm} ms")
    return tm / 1000


def randomized_offset(rng: secrets.SystemRandom, x: int, y: int, max_off: int, window_title: str = None, debug=True):
    w = window(window_title).topleft if window_title is not None else None

    ox = w.x + x if w is not None else x
    oy = w.y + y if w is not None else y

    nx = rng.randint(ox - max_off, ox + max_off)
    ny = rng.randint(oy - max_off, oy + max_off)

    if debug:
        print(f"Target: X: {nx}, Y: {ny}")

    return nx, ny


def window(name):
    return pyautogui.getWindowsWithTitle(name)[0]

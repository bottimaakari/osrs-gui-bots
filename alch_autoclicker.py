import secrets
import threading

import keyboard
import pyautogui


def mouse_info():
    pyautogui.mouseInfo()
    exit(0)


def randomized_sleep(minms, maxms):
    if minms > maxms:
        raise ValueError("Min must be less than max.")

    tm = rng.randint(minms, maxms)
    print(f"Delay for: {tm} ms")
    pyautogui.sleep(tm / 1000)
    return tm


def rand_mouse_speed(minms, maxms):
    if minms > maxms:
        raise ValueError("Min must be less than max.")
    tm = rng.randint(minms, maxms)
    print(f"Mouse speed: {tm} ms")
    return tm / 1000


def randomized_offset(x, y, use_window=True):
    ox = window.x + x if use_window else x
    oy = window.y + y if use_window else y

    return \
        rng.randint(ox - max_off, ox + max_off), \
        rng.randint(oy - max_off, oy + max_off)


def random_movement():
    for i in range(0, rng.randint(0, 5)):
        randomized_sleep(10, 30)
        x, y = randomized_offset(rng.randint(move_min, move_max), rng.randint(move_min, move_max), use_window=False)
        pyautogui.moveRel(x, y, rand_mouse_speed(20, 50))


def mouse_movement_background(arg):
    print("BG Thread started.")
    while running:
        randomized_sleep(10, 800)
        if not can_move:
            continue
        random_movement()
    print("BG Thread exiting.")


def hover_target(x, y):
    print(f"Hover target: ({x}, {y})")
    pyautogui.moveTo(x, y, rand_mouse_speed(mouse_min, mouse_max))


def click_target(x, y):
    print(f"Click target: ({x}, {y})")

    # Some random mouse movement before action
    # random_movement()

    global can_move
    can_move = False
    pyautogui.moveTo(x, y, rand_mouse_speed(mouse_min, mouse_max))
    pyautogui.leftClick()
    can_move = True

    # Some random mouse movement after action
    # random_movement()


def open_spell_menu():
    x, y = randomized_offset(745, 210)
    hover_target(x, y)
    randomized_sleep(50, 500)
    click_target(x, y)


def click_spell():
    x, y = randomized_offset(718, 328)
    hover_target(x, y)
    randomized_sleep(1200, 1300)
    click_target(x, y)


def click_item(item):
    x, y = randomized_offset(item[0], item[1])
    hover_target(x, y)
    randomized_sleep(30, 500)
    click_target(x, y)


def read_items():
    file = None

    try:
        file = open(items_file, "r")
    except IOError as exc:
        print(f"ERROR: Failed to read item file ({items_file}). Ensure it exists in the current directory.")
        raise exc

    data = []
    for line in file:
        line = line.strip()
        if line == "" or line[0] == "#":
            continue
        values = line.split(";")
        data.append([int(values[0]), int(values[1]), int(values[2])])

    file.close()
    return data


def save_items():
    file = None

    try:
        file = open(items_file, "r")
    except IOError as ex:
        print(
            f"ERROR: Failed to write into item file ({items_file}). Ensure this executable and the current user has "
            f"write permissions on this directory.")
        print(f"Exception details: {ex}")
        raise ex

    for it in items:
        file.write(str(it[0]) + ";" + str(it[1]) + ";" + str(it[2]))
        file.write("\r\n")  # TODO CRLF on win, LF on *nix

    file.close()


def interrupt(event):
    print("Interrupted.")
    global running
    running = False


try:
    # TODO enable for pos info
    # mouse_info()

    # Use system random data source
    rng = secrets.SystemRandom()

    # Mouse speed limits
    mouse_min = 50
    mouse_max = 300

    # Random movement offset limits
    move_min = -8
    move_max = 8

    # Maximum precise target offset
    max_off = 4

    # Collect game window info (topleft coords)
    window_name = "Rune"

    try:
        window = pyautogui.getWindowsWithTitle(window_name)[0].topleft
    except IndexError as ex:
        print("ERROR: Game client window was not detected. Ensure the game client is running first.")
        raise ex

    items_file = "items.txt"

    can_move = True
    running = True
    do_click_spell = True
    current = 0

    # Key 1 = ESC
    # Key 82 = NUMPAD 0
    keyboard.on_press_key(1, interrupt)

    print("Started. Hit ESC at any time to stop execution.")
    print("NOTE: Ensure item details are correctly set in items data file.")
    print("NOTE: Please do not move the mouse at all after the program has been started.")

    # Initial sleep for 1.5 sec
    print("Waiting 2 seconds..")
    randomized_sleep(2000, 2000)

    # (ITEM POSX, ITEM POSY, ITEM COUNT)
    items = read_items()

    if len(items) <= 0:
        print(f"ERROR: No items found in items file ({items_file}). Ensure items configured correctly first. See the "
              f"items example file for reference.")
        raise ValueError("No items defined in items file.")

    print("Read item data from items file.")

    move_thread = threading.Thread(target=mouse_movement_background, name="bg_mouse_movement", args=(None,))
    move_thread.start()

    # First, ensure spell menu open
    print("Opening spell menu..")
    open_spell_menu()

    # Start looping
    while running:
        # Must sleep enough between the moves
        # should be close to a constant value
        randomized_sleep(50, 80)

        print(f"do_click_spell: {do_click_spell}")

        # 33 % chance for ensuring spell menu is open
        # before clicking the spell
        if do_click_spell and rng.random() <= 0.33:
            open_spell_menu()

        if do_click_spell:
            click_spell()
            do_click_spell = False
            continue

        if current >= len(items):
            print("Out of items.")
            interrupt(None)
            break

        if items[current][2] <= 0:
            print(f"Item {current} out. Moving to next..")
            current += 1
            continue

        click_item(items[current])
        items[current][2] -= 1
        do_click_spell = True

    # Gracefully let the bg thread to exit
    move_thread.join()

    print("Sleeping 5 seconds before exiting..")
    randomized_sleep(5000, 5000)

except Exception as e:
    print("EXCEPTION OCCURRED DURING PROGRAM EXECUTION:")
    print(e)
    print("SLEEPING 10 SECONDS BEFORE EXITING..")
    randomized_sleep(10000, 10000)

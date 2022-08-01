import time

import keyboard


def press(key: keyboard.KeyboardEvent):
    print(f"KEY PRESSED: {key}")
    print(f"NAME: {key.name}")
    print(f"SCAN CODE: {key.scan_code}")

    if key.scan_code == 1:
        global running
        running = False


keyboard.on_press(press, False)

print("Press any key to get the key number.")
print("Press ESC to exit.")

running = True

while running:
    time.sleep(0.5)

print("Exiting.")

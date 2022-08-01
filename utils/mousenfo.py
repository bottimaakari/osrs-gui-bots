import pyautogui

window = pyautogui.getWindowsWithTitle("RuneLite")[0]

print(f"TOPLEFT: {window.topleft}")

pyautogui.mouseInfo()

import pytesseract
from guibot import finder as gfinder
from guibot import guibot as gbot
from guibot import target as gtarget

import common
import user_secrets

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

print(pytesseract)


def open_bank(bot: gbot.Region, booths: list) -> bool:
    common.hover_away(bot)

    # Try to find bank booth from screen
    for b in booths:
        img = common.as_image(b, 0.05)
        # If found, hover mouse to the booth and click it
        if bot.exists(img):
            print("BANK BOOTH FOUND")
            common.click_labeled_target(bot, b, "Bank Bank booth", 1)
            return True
    return False


def check_pin(bot: gbot.Region) -> bool:
    # tgt = gtarget.Text("Please enter your PIN", gfinder.TextFinder()).with_similarity(0.1)
    tgt = common.as_image('pin_screen', 0.1)

    common.hover_away(bot)

    if bot.exists(tgt):
        print("PIN SCREEN FOUND")
        return True
    else:
        print("PIN SCREEN NOT FOUND")
        return False


def solve_pin(bot: gbot.Region, pin: list):
    c = 0
    for p in pin:
        c += 1
        txt = gtarget.Text(str(p), gfinder.TextFinder()).with_similarity(0.5)
        img = common.as_image('pin_' + str(p), 0.1)

        # if bot.exists(txt):
        if bot.exists(img):
            print(f"FOUND DIGIT {c}")
            # common.click_text_target(bot, txt, 1, True)
            common.click_image_target(bot, img, 1, True)
        else:
            print(f"DIDNT FIND DIGIT {c}")
            raise Exception("Digit not found on screen.")


def bank_all_items(bot):
    pass


def bank_inventory(bot):
    pass


def test():
    fr, bot = common.init_bot(True)

    # Load booth image assets in random order
    booths = common.load_assets('booth_', fr, randomizeOrder=True)

    if not open_bank(bot, booths):
        print("FAILED TO OPEN BANK")
        return

    common.delay(False)

    if check_pin(bot):
        print("HAS PIN")
        # Create a file personal.py and add list variable with pin numbers: BANK_PIN = [first, second, third, fourth]
        solve_pin(bot, user_secrets.BANK_PIN)
    else:
        print("NO PIN CONFIGURED")

    bank_all_items(bot)


# TODO REMOVE
test()

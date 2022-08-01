from guibot import finder as gfinder
from guibot import guibot as gbot
from guibot import target as gtarget

import common
import user_secrets


def open_bank(bot: gbot.Region, booths: list) -> bool:
    for b in booths:
        if bot.exists(b):
            print("BANK BOOTH FOUND")
            common.click_text_target(bot, b, "Bank Bank Booth")
            return True
    return False


def check_pin(bot: gbot.Region) -> bool:
    tgt = gtarget.Text("Please enter your PIN", bot.cv_backend())

    if bot.exists(tgt):
        print("PIN TEXT FOUND")
        return True
    else:
        return False


def solve_pin(bot: gbot.Region, pin: list):
    pass


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

    if check_pin(bot):
        print("HAS PIN")
        # Create a file personal.py and add list variable with pin numbers: BANK_PIN = [first, second, third, fourth]
        solve_pin(bot, user_secrets.BANK_PIN)
    else:
        print("NO PIN CONFIGURED")

    bank_all_items()


# TODO REMOVE
test()

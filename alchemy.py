from guibot import finder as gfinder
from guibot import guibot as gbot
from guibot import target as gtarget

import common


def cast_spell(bot: gbot.Region, click: bool = True):
    found = False
    
    img = common.as_image('spell', 0.1)
    
    if bot.exists(img):
        print("FOUND SPELL")
        found = True
        if click:
            common.click_image_target(bot, img, 1, True)
            common.hover_away(bot)
        return True
    else:
        print("SPELL NOT FOUND")
        return False
        
    # Keep looping (without clicking), until spell not found anymore
    # if found:
    #     cast_spell(bot, False)


def find_item(bot: gbot.Region, items: list, click: bool = True):
    found = False
    
    for it in items:
        img = common.as_image(it, 0.1)
        if bot.exists(img):
            print("FOUND NOTE")
            found = True
            if click:
                common.click_image_target(bot, img, 1, True)
                common.hover_away(bot)
            return True
        else:
            print("NOTE(S) NOT FOUND")
            return False
        
    # Check once again
    # If still found, keep looping until not found anymore
    # To wait for the other view
    # if found:
    #     find_item(bot, items)


def open_magic_menu(bot):
    img = common.as_image('magic_menu', 0.1)

    if bot.exists(img):
        print("FOUND MENU")
        common.click_image_target(bot, img, 1, True)
        common.hover_away(bot)
        return True
    else:
        print("MENU NOT FOUND")
        return False


def run():
    fr, bot = common.init_bot(True)

    # Load booth image assets in random order
    notes = common.load_assets('note_', fr, randomizeOrder=True)
    
    mode = 0

    while True:
        if mode == 0:
            common.delay(False)
        else:
            common.delay(False, 200, 500)
        
        print("LOOPING")
        print(f"MODE: {mode}")
        
        if mode == 0:
            if not cast_spell(bot):
                print("COULD NOT CAST SPELL")

                print("TRYING TO OPEN MAGIC MENU")
                if not open_magic_menu(bot):
                    print("FAILED TO OPEN MENU")
                    return
                else:
                    print("MAGIC MENU OPEN")
                    if not cast_spell(bot):
                        print("STILL FAILED TO CAST")
                        return
                    else:
                        print("CAST SUCCEEDED")
                        mode = 1
                        continue
            else:
                print("SPELL IS CAST")
                mode = 1
                continue
            
        if mode == 1:
            if not find_item(bot, notes):
                print("DID NOT FIND ANY NOTES")
                return
            else:
                print("CASTED SPELL ON NOTE")
                mode = 0
                continue


# TODO REMOVE
run()

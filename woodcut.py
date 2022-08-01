from time import perf_counter, sleep

from guibot import guibot as gbot
from guibot import region as bregion
from guibot import target as btarget

import common

def run():
    fr, bot = common.init_bot(True)

    # Collect stump tree image assets
    stumps = common.load_assets('yew_stump_', fr, True)
    print("STUMPS LOADED: " + str(len(stumps)))

    # Collect live tree image assets
    trees = common.load_assets('yew_', fr, True)
    print("TREES LOADED: " + str(len(trees)))

    # Initially, player is not cutting
    # TODO somehow determine if the player is currently cuttiing or not
    cutting = False

    while True:
        common.delay(long=False)

        print("STATUS: ", end="")
        print("CUTTING" if cutting else "IDLE")

        items = None

        try:
            items = bot.find_all('yew_log_1', allow_zero=True)
            print("LOGS COUNT: " + str(len(items)))
        except:
            items = None

        # Check if we have 28 logs in inv
        if (items and len(items) >= 28):
            print("INV FULL")
            common.delay(True, 58219)  # TODO remove, set default limit higher
            continue

        stump = None

        for s in stumps:
            img = btarget.Image(s).with_similarity(0.1)
            if bot.exists(img):
                stump = s
                break

        if (stump):
            print("STUMP EXISTS")
            cutting = False
            continue

        else:
            print("STUMP NOT FOUND")

        tree = None

        # Tree image filenames in random order
        common.rng.shuffle(trees)

        # Search for the tree object
        for t in trees:
            img = btarget.Image(t).with_similarity(0.1)
            if bot.exists(img):
                print("TREE FOUND")
                tree = t
                break

        if (cutting and tree):
            common.delay(long=True)

            # 33% prob
            if common.rand_bool(0.33):
                print("EXTRA CLICK")
                try:
                    common.click_text_target(bot, tree, 'Chop Down Yew')
                except:
                    print("TREE NO LONGER EXISTS")
                    tree = None
            continue

        elif (tree):
            common.delay(long=True)
            print("START CUTTING")
            try:
                common.click_text_target(bot, tree, 'Chop Down Yew')
            except:
                print("TREE NO LONGER EXISTS")
                tree = None
            cutting = True
            continue

        else:
            print("TREE NOT FOUND")
            continue

run()

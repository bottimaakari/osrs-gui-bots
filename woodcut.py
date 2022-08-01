from time import perf_counter, sleep

from guibot import guibot as gbot
from guibot import region as bregion
from guibot import target as btarget

import common


def click_text_target(bot: gbot.Region, target, text: str):
    if bot.exists(target):
        bot.hover(target)
    else:
        print("CLICK TARGET LOST")
        return

    text = bregion.Text(text, bot.cv_backend()).with_similarity(0.5)

    if bot.exists(text):
        # Minor random delay before clicking
        print(f"LABEL {text} FOUND")
        common.delay(False)

        for i in range(common.click_count()):
            common.micro_delay()
            bot.click(target)
            print(f"CLICKED {target}")
    else:
        print(f"LABEL {text} NOT FOUND")


def run():
    fr, bot = common.init_bot(True)

    stumps = []
    trees = []

    # Collect stump tree image assets
    for i in range(1, 100):
        fn = 'yew_stump_' + str(i)
        try:
            fr.search(fn)
            stumps.append(fn)
        except:
            pass

    # Collect live tree image assets
    for i in range(1, 100):
        fn = 'yew_' + str(i)
        try:
            fr.search(fn)
            trees.append(fn)
        except:
            pass

    print("TREES: " + str(len(trees)))
    print("STUMPS: " + str(len(stumps)))

    # Initially not cutting
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
                    click_text_target(bot, tree, 'Chop Down Yew')
                except:
                    print("TREE NO LONGER EXISTS")
                    tree = None
            continue

        elif (tree):
            common.delay(long=True)
            print("START CUTTING")
            try:
                click_text_target(bot, tree, 'Chop Down Yew')
            except:
                print("TREE NO LONGER EXISTS")
                tree = None
            cutting = True
            continue

        else:
            print("TREE NOT FOUND")
            continue

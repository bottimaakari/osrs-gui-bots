import random
import secrets
from time import perf_counter, sleep

import guibot
from guibot import config as bconfig
from guibot import fileresolver as bfileres
from guibot import finder as bfinder
from guibot import guibot as gbot
from guibot import region as bregion
from guibot import target as btarget
from guibot.config import GlobalConfig
from guibot.fileresolver import FileResolver
from guibot.finder import TextFinder
from guibot.region import Region
from guibot.target import Image, Text

import mouse

rng = secrets.SystemRandom()


def event_loop():
    pass


def init_bot(region: bool):
    GlobalConfig.image_quality = 0
    GlobalConfig.smooth_mouse_drag = False
    
    if region:
        pos = mouse.get_window_pos()

        fr = gbot.FileResolver()
        reg = gbot.Region(pos[0], pos[1], pos[2], pos[3])
        
        fr.add_path('img/')

        return (fr, reg)
    else:
        bot = gbot.GuiBot()

        bot.add_path('img/')

        return bot


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
        delay(False)

        for i in range(click_count()):
            micro_delay()
            bot.click(target)
            print(f"CLICKED {target}")
    else:
        print(f"LABEL {text} NOT FOUND")


def click_count():
    return rng.randint(1, 5)


def mouse_speed():
    return rng.randint(83, 241)


def micro_delay():
    tm = rng.randint(11, 91) / 1000
    sleep(tm)


def delay(long: bool, max=None):
    if max is not None and max <= 1000:
        max = None
    
    tm = None

    if long:
        # ~1 sec -- ~10 sec
        tm = rng.randint(927, 11352 if max is None else max) / 1000  # TODO higher max (4min)
    else:
        # ~ 1sec
        tm = rng.randint(913, 1185 if max is None else max) / 1000

    sleep(tm)


def click_offset():
    pass


def rand_bool(prob) -> bool:
    return rng.random() <= prob


def run():
    fr, bot = init_bot(True)

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
        delay(long=False)

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
            delay(True, 58219) # TODO remove, set default limit higher
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
        rng.shuffle(trees)
        
        # Search for the tree object
        for t in trees:
            img = btarget.Image(t).with_similarity(0.1)
            if bot.exists(img):
                print("TREE FOUND")
                tree = t
                break

        if (cutting and tree):
            delay(long=True)

            # 33% prob
            if rand_bool(0.33):
                print("EXTRA CLICK")
                try:
                    click_text_target(bot, tree, 'Chop Down Yew')
                except:
                    print("TREE NO LONGER EXISTS")
                    tree = None
            continue

        elif (tree):
            delay(long=True)
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

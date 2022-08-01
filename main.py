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
        pos = mouse.get_pos()

        fr = gbot.FileResolver()
        reg = gbot.Region(pos[0], pos[1], pos[2], pos[3])
        
        fr.add_path('img/')

        return (fr, reg)
    else:
        bot = gbot.GuiBot()

        bot.add_path('img/')

        return bot


def start_cutting(bot: gbot.Region, target):
    bot.hover(target)
    
    text = bregion.Text('Chop Down Yew', bfinder.Finder()).with_similarity(0.5)
    
    if bot.exists(text):
        print("CUT LABEL FOUND")
        bot.click(target)
    else:
        print("CUT LABEL NOT FOUND")


def mouse_speed():
    return rng.randint(83, 241)


def delay(long: bool):
    tm = None

    if long:
        tm = rng.randint(927, 10358) / 1000  # TODO
    else:
        tm = rng.randint(947, 1234) / 1000

    sleep(tm)


def click_delay():
    return rng.randint(512, 5221) / 1000


def click_offset():
    pass


def rand_bool(prob) -> bool:
    return rng.random() <= prob


def main():
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

        # Check if we have 24 logs in inv
        if (items and len(items) >= 28):
            print("INV FULL")
            break

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
            if rand_bool(0.33):
                delay(long=True)
                print("EXTRA CLICK")
                try:
                    start_cutting(bot, tree)
                except:
                    print("TREE NO LONGER EXISTS")
                    tree = None
            continue
        elif (tree):
            print("START CUTTING")
            delay(long=True)
            try:
                start_cutting(bot, tree)
            except:
                print("TREE NO LONGER EXISTS")
                tree = None
            cutting = True
            continue
        else:
            print("TREE NOT FOUND")
            continue


main()

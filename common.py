import secrets
from time import sleep

from guibot import config as gconfig
from guibot import finder as gfinder
from guibot import guibot as gbot
from guibot import location as glocation
from guibot import region as gregion
from guibot import target as gtarget

import mouse

rng = secrets.SystemRandom()


def click_count(max):
    return rng.randint(1, max + 1)


def mouse_speed():
    return rng.randint(83, 241)


def micro_delay():
    tm = rng.randint(11, 91) / 1000
    print("DELAY: " + str(tm) + " SEC")
    sleep(tm)


def delay(long: bool, max=None):
    # Ensure max at least 1 sec or most 5min (afk kick time)
    if max is not None and (max <= 1000 or max > 280000):
        max = None

    tm = None

    if long:
        # ~1 sec -- ~10 sec
        tm = rng.randint(927, 11352 if max is None else max) / \
            1000  # TODO higher max (4min)
    else:
        # ~ 1sec
        tm = rng.randint(913, 1185 if max is None else max) / 1000

    print("DELAY: " + str(tm) + " SEC")
    sleep(tm)


def click_offset():
    pass


def rand_bool(prob) -> bool:
    return rng.random() <= prob


def init_bot(use_region: bool):
    gconfig.GlobalConfig.image_quality = 0
    gconfig.GlobalConfig.smooth_mouse_drag = False

    if use_region:
        pos = get_window_pos("RuneLite")

        fr = gbot.FileResolver()
        reg = gbot.Region(pos[0], pos[1], pos[2], pos[3])

        # for some reason only parent dir
        # or wildcards dont work
        # TODO figure out how to import all subdirs
        fr.add_path('assets/bank')
        fr.add_path('assets/inventory')
        fr.add_path('assets/yew')

        return (fr, reg)
    else:
        bot = gbot.GuiBot()
        bot.add_path('assets/')
        return bot


def load_assets(name_prefix: str, fr: gbot.FileResolver, randomizeOrder: bool):
    assets = []

    # Collect bank booth image assets
    for i in range(0, 100):
        fn = name_prefix + str(i)
        try:
            fr.search(fn)
            assets.append(fn)
        except:
            pass

    if len(assets) <= 0:
        print(f"WARNING: NO ASSETS FOUND WITH PREFIX: '{name_prefix}'")
        return assets

    if randomizeOrder:
        rng.shuffle(assets)

    return assets


def hover_away(bot: gbot.Region):
    delay(False)
    bot.hover(bot.top_left)


def click_text_target(bot: gbot.Region, target: gtarget.Text, max_count: int = 1, hover: bool = True):
    # First, move the mouse out of the way
    if hover:
        hover_away(bot)
    
    delay(False)
    if bot.exists(target):
        bot.hover(target)
    else:
        print("CLICK TARGET LOST")
        return

    # text = gtarget.Text(text, gfinder.TextFinder()).with_similarity(0.1)

    delay(False)
    if bot.exists(target):
        # Minor random delay before clicking
        print(f"LABEL {target.value} FOUND")

        for _ in range(0, click_count(max_count)):
            micro_delay()
            bot.click(target)
            print(f"CLICKED {target.value}")

    else:
        print(f"LABEL {target.value} NOT FOUND")


def click_labeled_target(bot: gbot.Region, target, text: str, max_count: int = 1):
    # First, move the mouse out of the way
    hover_away(bot)
    
    delay(False)
    if bot.exists(target):
        bot.hover(target)
    else:
        print("CLICK TARGET LOST")
        return

    # text = gtarget.Text(text, gfinder.TextFinder()).with_similarity(0.1)

    # click_text_target(bot, text, max_count, hover=False)
    click_text_target(bot, target, max_count, hover=False)


# Returns the given object name as finder image with given similarity
def as_image(name, similarity):
    return gtarget.Image(name).with_similarity(similarity)


def get_window_pos(name):
    return mouse.get_window_pos(name)


# Loads bot configuration from given file path, into dict<str, str>
def load_configuration(path) -> dict:
    pass

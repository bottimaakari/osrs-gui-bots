import secrets

from time import sleep

from guibot import config as gconfig
from guibot import guibot as gbot
from guibot import target as gtarget
from guibot import region as gregion

import mouse

rng = secrets.SystemRandom()


def click_count():
    return rng.randint(1, 5)


def mouse_speed():
    return rng.randint(83, 241)


def micro_delay():
    tm = rng.randint(11, 91) / 1000
    sleep(tm)


def delay(long: bool, max: int = None):
    # Ensure max at least 1 sec or most 5min (afk kick time)
    if max is not None and max <= 1000 or max > 280000:
        max = None

    tm = None

    if long:
        # ~1 sec -- ~10 sec
        tm = rng.randint(927, 11352 if max is None else max) / \
            1000  # TODO higher max (4min)
    else:
        # ~ 1sec
        tm = rng.randint(913, 1185 if max is None else max) / 1000

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

        fr.add_path('assets/')

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


def click_text_target(bot: gbot.Region, target, text: str):
    if bot.exists(target):
        bot.hover(target)
    else:
        print("CLICK TARGET LOST")
        return

    text = gtarget.Text(text, bot.cv_backend()).with_similarity(0.2)

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


# Returns the given object name as finder image with given similarity 
def as_image(name, similarity):
    return gtarget.Image(name).with_similarity(similarity)


def get_window_pos(name):
    return mouse.get_window_pos(name)


# Loads bot configuration from given file path, into dict<str, str>
def load_configuration(path) -> dict:
    pass
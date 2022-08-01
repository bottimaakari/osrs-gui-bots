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
    return rng.randint(1, max)


def mouse_speed():
    return rng.randint(80, 240)


def micro_delay():
    tm = rng.randint(30, 90) / 1000
    print("DELAY: " + str(tm) + " SEC")
    sleep(tm)


def delay(long: bool, minn=None, maxx=None):
    if minn is not None and minn < 100:
        minn = None

    # Ensure max at least 1 sec or most 5min (afk kick time)
    if maxx is not None and (maxx > 280000):
        maxx = None

    if minn is not None and maxx is not None and minn > maxx:
        print("MIN cannot be larger than MAX")

    tm = None

    if long:
        # ~1 sec -- ~10 sec
        # TODO higher max (4min)
        tm = rng.randint(900 if minn is None else minn, 11000 if maxx is None else maxx) / 1000
    else:
        # ~ 1sec
        tm = rng.randint(900 if minn is None else minn, 1100 if maxx is None else maxx) / 1000

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
        fr.add_path('assets/alchemy')
        fr.add_path('assets/bank')
        fr.add_path('assets/inventory')
        fr.add_path('assets/yew')

        return fr, reg
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
    micro_delay()
    bot.hover(bot.top_left)


def click_text_target(bot: gbot.Region, target: gtarget.Text, max_count: int = 1, hover: bool = True):
    # First, move the mouse out of the way
    if hover:
        hover_away(bot)

    micro_delay()
    bot.hover(target)

    micro_delay(False)

    # Minor random delay before clicking
    for _ in range(0, click_count(max_count)):
        micro_delay()
        bot.click(target)
        print(f"CLICKED TEXT TARGET")


def click_image_target(bot: gbot.Region, target: gtarget.Image, max_count: int = 1, hover: bool = True):
    # First, move the mouse out of the way
    if hover:
        hover_away(bot)

    micro_delay()
    if bot.exists(target):
        bot.hover(target)
    else:
        print("CLICK TARGET LOST")
        return

    micro_delay()
    if bot.exists(target):
        print(f"IMAGE TARGET FOUND")

        # Minor random delay before clicking
        for _ in range(0, click_count(max_count)):
            micro_delay()
            bot.click(target)
            print(f"CLICKED IMAGE TARGET")

    else:
        print(f"IMAGE TARGET WAS NOT FOUND")


def click_labeled_target(bot: gbot.Region, target, label: str, max_count: int = 1):
    # First, move the mouse out of the way
    hover_away(bot)

    micro_delay()
    if bot.exists(target):
        bot.hover(target)
    else:
        print("CLICK TARGET LOST")
        return

    # TODO fix text target recognition speed

    # label_tgt = gtarget.Text(label, gfinder.TextFinder()).with_similarity(0.1)

    # delay(False)

    # if bot.exists(label_tgt):
    #     print(f"LABEL {label} FOUND")
    #     click_image_target(bot, target, max_count, False)
    # else:
    #     print(f"LABEL {label} WAS NOT FOUND")

    click_image_target(bot, target, max_count, False)


# Returns the given object name as finder image with given similarity
def as_image(name, similarity):
    return gtarget.Image(name).with_similarity(similarity)


def get_window_pos(name):
    return mouse.get_window_pos(name)


# Loads bot configuration from given file path, into dict<str, str>
def load_configuration(path) -> dict:
    pass

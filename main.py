import woodcut
import combat

def main(*args):
    if len(args) < 1:
        print("ERROR: Please give bot name as argument.")
        return
    
    bot_name = args[0]

    print("STARTING BOT: " + args[0])
    
    if bot_name == "woodcut":
        woodcut.run()
    elif bot_name == "combat":
        combat.run()
    else:
        print("Name of the bot not recognized.")
        return

# main("woodcut")

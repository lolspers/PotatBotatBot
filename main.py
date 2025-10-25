
import json
import threading
import queue

from datetime import datetime
from colorama import Fore, Style, Back
from time import time, sleep, strftime

import api
from config import config
from logger import logger, cprint, clprint
from utils import rankPrice, relative


with open("quizes.json", "r") as file:
    quizes = json.loads(file.read())



loopDelay: int = 1
executions: float = 0

allFarmingCommands: list[str] = ["potato", "steal", "trample", "cdr", "quiz"]
allShopItems: list[str] = ["shop-fertilizer", "shop-guard", "shop-cdr", "shop-quiz"]

executedCommand: bool = True
boughtShopItem: bool = True


uInputs = queue.Queue()


def inputs():
    logger.debug("Started input loop")

    while True:
        uInput = input().lower()
        uInputs.put(uInput)

        if uInput == "s":
            logger.info("Stopped input loop by users request")
            break


        elif uInput in allFarmingCommands:
            enabled = config.toggleCommand(uInput)
            
            cprint(f"{"Enabled" if enabled else "Disabled"} command '{uInput}'", fore=Fore.CYAN)


        elif uInput in allShopItems:
            enabled = config.toggleCommand(uInput)

            cprint(f"{"Enabled" if enabled else "Disabled"} auto buying for '{uInput}'", fore=Fore.CYAN)


        elif "twitch" in uInput:
            enabled = config.enableTwitch()

            if not enabled:
                cprint("Cannot enable twitch api: A required twitch credential in is not set in the config!", fore=Fore.MAGENTA)

            else:
                cprint("Switched to twitch messages", fore=Fore.CYAN)


        elif uInput == "potat" or uInput == "potatbotat":
            enabled = config.enablePotat()

            if not enabled:
                cprint("Cannot enable potat api: potatToken is not set in the config!", fore=Fore.MAGENTA)

            else:
                cprint("Switched to potat api", fore=Fore.CYAN)


        elif uInput == "refresh":
            logger.info("User requested a cooldown refresh")

            cprint("Refreshing cooldowns...", fore=Fore.CYAN)


        elif uInput == "color":
            enabled = config.toggleColoredPrinting()

            cprint(f"{"Enabled" if enabled else "Disabled"} printing in color", fore=Fore.CYAN)


        else:
            logger.debug(f"Invalid user command: {uInput}")

            cprint(f"Invalid command: '{uInput}'", fore=Fore.YELLOW)

        print("\n")



inputThread = threading.Thread(target=inputs, daemon=True)
inputThread.start()



cprint("Type at any time to execute a command", style=Style.DIM)
cprint("Valid commands:", style=Style.DIM)
cprint("'s': Stop the bot and close the program\n"
    "'potat': Change to potatbotat api\n"
    "'twitch': Change to twitch api", fore=Fore.GREEN, style=Style.DIM)


longestFarmingCommand = len(max(allShopItems, key=len))
for command in allFarmingCommands:
    cprint(f"{f"'{command}': Toggle auto farming for {command}": <{longestFarmingCommand*2+20}} (Currently set to {config.isEnabled(command)})", fore=Fore.GREEN, style=Style.DIM)

longestShopItem = len(max(allShopItems, key=len))
for item in allShopItems:
    cprint(f"{f"'{item}': Toggle auto buying from the shop for {item.split("shop-", 1)[1]}": <{longestShopItem*2+40}} (Currently set to {config.isEnabled(item)})", fore=Fore.GREEN, style=Style.DIM)

cprint("'refresh': Force refresh potatbotat cooldowns\n", fore=Fore.GREEN, style=Style.DIM)
cprint("'color': Toggle printing in color\n", fore=Fore.GREEN, style=Style.DIM)
cprint("Manual changes to config requires a restart to update\n", fore=Fore.GREEN)


logger.debug("Started bot")

while True:
    try:
        if executions > 20:
            logger.warning("Hit client-side ratelimit")
            cprint(f"{strftime("%H:%M:%S")} Hit client-side ratelimit, paused for 1h until {datetime.fromtimestamp(time() + 3600).strftime("%H:%M:%S")} - commands will not work during this time", fore=Fore.RED)

            executions = 0
            sleep(3600)

            logger.debug("Resumed bot")
            cprint("Resumed", fore=Fore.CYAN, style=Style.DIM)


        if not uInputs.empty():
            uInput = uInputs.get()
            if uInput == "s":
                logger.info("Stopped bot by users request")
                break

            elif uInput in allFarmingCommands:
                executedCommand = True

            elif uInput in allShopItems:
                boughtShopItem = True

            elif "refresh" in uInput:
                executedCommand = True
                boughtShopItem = True


        if boughtShopItem:
            executions += 2
            shopCooldowns = api.getShopCooldowns()
            boughtShopItem = False


        if executedCommand:
            executions += 1
            potatoData = api.getPotatoData()

            potatoes: int = potatoData["potatoes"]
            rank: int = potatoData["rank"]
            prestige: int = potatoData["prestige"]

            rankCost: int = rankPrice(prestige, rank)

            cooldowns: dict[str, int] = potatoData["cooldowns"]


            logger.debug("Refreshed cooldowns")
            print("Refreshed cooldowns\n")

            for command, cooldown in cooldowns.items():
                readyIn = relative(cooldown)

                cprint(f"{command}: {readyIn}", style=Style.DIM if "in" in readyIn else None)
            

            executedCommand = False

            if potatoes >= rankCost:
                if rank == 6:
                    ok, response = api.send("prestige")

                    if not ok:
                        clprint("Failed to prestige", response, style=[Style.BRIGHT], globalFore=Fore.RED)

                    else:
                        clprint("Successfully prestiged:", response, style=[Style.BRIGHT], globalFore=Fore.YELLOW)

                else:
                    ok, response = api.send("rankup")

                    if not ok:
                        clprint("Failed to rank up:", response, style=[Style.BRIGHT], globalFore=Fore.RED)

                    else:
                        clprint("Successfully ranked up:", response, style=[Style.BRIGHT], globalFore=Fore.YELLOW)
                

                executedCommand = True


        currentTime = time()
        for cooldown in cooldowns:
            if currentTime < cooldowns[cooldown]:
                continue

            executions += 1
            executedCommand = True
            if cooldown != "quiz":
                if cooldown == "potato":
                    if shopCooldowns.get("shop-fertilizer", time()+10) < time():
                        boughtShopItem = api.buyItem(item="fertilizer", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem
                    
                    if shopCooldowns.get("shop-guard", time()+10) < time():
                        if boughtShopItem:
                            sleep(5) 
                        
                        boughtShopItem = api.buyItem(item="guard", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem


                ok, response = api.send(cooldown)

                if not ok:
                    clprint("Failed to execute command:", response, style=[Style.BRIGHT], globalFore=Fore.RED)

                else:
                    clprint("Executed command:", response, style=[None, Style.DIM])


                if cooldown == "cdr":
                    if shopCooldowns.get("shop-cdr", time()+10) < time():
                        if boughtShopItem:
                            sleep(5) 
                        
                        boughtShopItem = api.buyItem(item="cdr", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem

                sleep(1)
                continue


            # first execute the quiz in the targetted twitch chat
            # to not send "🥳 Thats right! Congratulations on getting the right answer, heres # potatoes!" in your own chat
            ok, response = api.twitchSend("quiz")
            cprint(response, fore=None if ok else Fore.RED)
            sleep(5)

            ok, quiz = api.potatSend("quiz", cdRetries=3)

            if not ok:
                logger.warning(f"Failed to get quiz: {quiz}")
                clprint("Failed to get quiz:", quiz, style=[Style.BRIGHT], globalFore=Fore.RED)
                continue


            # Example response:󠀀 ⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: <quiz>
            clprint("Received quiz:", quiz, style=[None, Style.DIM])
            answer = quizes.get(quiz, None)

            if answer is None:
                logger.warning(f"No quiz anser found for quiz: {quiz}")
                clprint("No quiz answer found for quiz:", quiz, style=[Style.BRIGHT], globalFore=Fore.RED)
                continue
            

            clprint("Found quiz answer:", answer, style=[Style.BRIGHT])

            sleep(5) # small cooldown to be safe
            ok, response = api.twitchSend(f"{answer}", prefix=False)

            if not ok:
                clprint("Failed to answer quiz:", response, style=[None, Style.DIM])
            
            else:
                clprint("Answered quiz:", response, style=[None, Style.DIM], globalFore=Fore.GREEN)


            if shopCooldowns.get("shop-quiz", time()+10) < time():
                if boughtShopItem:
                    sleep(5)
                
                boughtShopItem = api.buyItem(item="quiz", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem

            executions += 2
            continue


        executions -= loopDelay/10 if loopDelay < 90 else 0.9

        sleep(loopDelay)



    except api.stopBot as e:
        logger.critical(f"Stopped bot: {e}")
        clprint("Stopped bot:", e, style=[Style.BRIGHT, None], globalFore=Fore.MAGENTA)

        cprint("Press enter to exit.", style=Style.DIM)
        input()


    except Exception as e:
        executions += 1
        clprint("Error:", e, style=[Style.BRIGHT], globalFore=Fore.RED)

        logger.error(f"Caught exception in main", exc_info=e)

        sleep(5)
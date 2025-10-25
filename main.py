
import json
import threading
import queue
import colorama

colorama.init(autoreset=True)

from colorama import Fore, Style
from datetime import datetime
from time import time, sleep, strftime

import api
from config import config
from logger import logger
from priceUtils import rankPrice


with open("quizes.json", "r") as file:
    quizes = json.loads(file.read())


potatData = {}
cooldowns = []

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
            
            print(Fore.CYAN + f"{"Enabled" if enabled else "Disabled"} command '{uInput}'")


        elif uInput in allShopItems:
            enabled = config.toggleCommand(uInput)

            print(Fore.CYAN + f"{"Enabled" if enabled else "Disabled"} auto buying for '{uInput}'")


        elif "twitch" in uInput:
            enabled = config.enableTwitch()

            if not enabled:
                print(Fore.MAGENTA + "Cannot enable twitch api: A required twitch credential in is not set in the config!")

            else:
                print(Fore.CYAN + "Switched to twitch messages")


        elif uInput == "potat" or uInput == "potatbotat":
            enabled = config.enablePotat()

            if not enabled:
                print(Fore.MAGENTA + "Cannot enable potat api: potatToken is not set in the config!")

            else:
                print(Fore.CYAN + "Switched to potat api")


        elif uInput == "refresh":
            logger.info("User requested a cooldown refresh")

            print(Fore.CYAN + "Refreshing cooldowns...")


        else:
            logger.debug(f"Invalid user command: {uInput}")

            print(Fore.CYAN + f"Invalid command: '{uInput}'")

        print("\n")



inputThread = threading.Thread(target=inputs, daemon=True)
inputThread.start()



print(Style.DIM + "Type at any time to execute a command")
print(Style.DIM + "Valid commands:")
print(Style.DIM + Fore.GREEN + "'s': Stop the bot and close the program\n"
    "'potat': Change to potatbotat api\n"
    "'twitch': Change to twitch api")


longestFarmingCommand = len(max(allShopItems, key=len))
for command in allFarmingCommands:
    print(Style.DIM + Fore.GREEN + f"{f"'{command}': Toggle auto farming for {command}": <{longestFarmingCommand*2+20}} (Currently set to {config.isEnabled(command)})")

longestShopItem = len(max(allShopItems, key=len))
for item in allShopItems:
    print(Style.DIM + Fore.GREEN + f"{f"'{item}': Toggle auto buying from the shop for {item.split("shop-", 1)[1]}": <{longestShopItem*2+40}} (Currently set to {config.isEnabled(item)})")

print(Style.DIM + Fore.GREEN + "'refresh': Force refresh potatbotat cooldowns\n")
print(Fore.GREEN + "Manual changes to config requires a restart to update\n")


logger.debug("Started bot")

while True:
    try:
        if executions > 20:
            logger.warning("Hit client-side ratelimit")
            print(Fore.RED + f"{strftime("%H:%M:%S")} Hit client-side ratelimit, paused for 1h until {datetime.fromtimestamp(time() + 3600).strftime("%H:%M:%S")} - commands will not work during this time")

            executions = 0
            sleep(3600)

            logger.debug("Resumed bot")


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

            potatoes = potatoData["potatoes"]
            rank = potatoData["rank"]
            prestige = potatoData["prestige"]

            rankCost = rankPrice(prestige, rank)

            cooldowns = potatoData["cooldowns"]

            logger.debug("Refreshed cooldowns")
            print(Style.DIM + "Refreshed cooldowns\n")

            executedCommand = False

            if potatoes >= rankCost:
                if rank == 6:
                    ok, response = api.send("prestige")

                    if not ok:
                        print(Style.DIM + Fore.RED + f"Failed to prestige: {response}")

                    else:
                        print(Fore.YELLOW + f"Successfully prestiged: {response}")

                else:
                    ok, response = api.send("rankup")

                    if not ok:
                        print(Style.DIM + Fore.RED + f"Failed to rank up: {response}")

                    else:
                        print(Style.BRIGHT + Fore.YELLOW + f"Successfully ranked up: {response}")
                

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
                    print(Fore.RED + f"Failed to execute command: {response}")

                else:
                    print(f"Executed command: {response}")


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
            print(response if ok else Fore.RED + response)
            sleep(5)

            ok, quiz = api.potatSend("quiz", cdRetries=3)

            if not ok:
                logger.warning(f"Failed to get quiz: {quiz}")
                print(Fore.RED + f"Failed to get quiz: {quiz}")
                continue


            # Example response:󠀀 ⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: <quiz>
            print(Style.DIM + f"Received quiz: {quiz}")
            answer = quizes.get(quiz, None)

            if answer is None:
                logger.warning(f"No quiz anser found for quiz: {quiz}")
                print(Fore.RED + f"No quiz answer found for quiz: {quiz}")
                continue
            

            print(Style.DIM + f"Found quiz answer: {answer}")

            sleep(5) # small cooldown to be safe
            ok, response = api.twitchSend(f"{answer}", prefix=False)

            if not ok:
                print(Fore.RED + f"Failed to answer quiz: {response}")
            
            else:
                print(Style.DIM + Fore.GREEN + f"Answered quiz: {response}")


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
        print(Style.BRIGHT + Fore.MAGENTA + f"Stopped bot: {e}")

        input(Style.DIM + "Press enter to exit.")


    except Exception as e:
        executions += 1
        print(Style.DIM + Fore.RED + f"ERROR: {e}")

        logger.error(f"Caught exception in main", exc_info=e)

        sleep(5)
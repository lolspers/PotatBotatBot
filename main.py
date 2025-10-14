
import json
import threading
import queue

from time import time, sleep, strftime

import api
from config import loopDelay, executedCommand, boughtShopItem, executions, allFarmingCommands, allShopItems
from data import getConfig, updateConfig
from logger import logger
from priceUtils import rankPrice


with open("quizes.json", "r") as file:
    quizes = json.loads(file.read())

config = getConfig()

potatData = {}
cooldowns = []

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
            newValue = bool(config["farmingCommands"][uInput] is False)
            config["farmingCommands"][uInput] = newValue

            api.farmingCommands = config["farmingCommands"]
            updateConfig(config)

            logger.info(f"Toggled command '{uInput}', set to {newValue}")
            print(f"{"Enabled" if newValue is True else "Disabled"} command '{uInput}'")


        elif uInput in allShopItems:
            newValue = bool(config["shopItems"][uInput] is False)
            config["shopItems"][uInput] = newValue

            api.shopItems = config["shopItems"]
            updateConfig(config)

            logger.info(f"Toggled auto buying for '{uInput}', set to {newValue}")
            print(f"{"Enabled" if newValue else "Disabled"} auto buying for '{uInput}'")


        elif "twitch" in uInput:
            api.usePotatApi = False
            config["usePotatApi"] = False
            updateConfig(config)

            logger.info("Enabled sending messages on twitch")
            print("Switched to twitch messages")


        elif uInput == "potat" or uInput == "potatbotat":
            api.usePotatApi = True
            config["usePotatApi"] = True
            updateConfig(config)

            logger.info("Enabled sending messages through potat api")
            print("Switched to potat api")


        elif uInput == "refresh":
            logger.info("User requested to refresh cooldowns")
            print("Refreshing cooldowns...")


        else:
            logger.debug(f"Invalid user command: {uInput}")
            print(f"Invalid command: '{uInput}'")

        print("\n")


inputThread = threading.Thread(target=inputs, daemon=True)
inputThread.start()


print("Type at any time to execute a command")
print("Valid commands:")
print("'s': Stop the bot and close the program")
print("'potat': Change to potatbotat api")
print("'twitch': Change to twitch api")

longestFarmingCommand = len(max(allShopItems, key=len))
for command in allFarmingCommands:
    print(f"{f"'{command}': Toggle auto farming for {command}": <{longestFarmingCommand*2+20}} (Currently set to {config["farmingCommands"][command]})")

longestShopItem = len(max(allShopItems, key=len))
for item in allShopItems:
    print(f"{f"'{item}': Toggle auto buying from the shop for {item.split("shop-", 1)[1]}": <{longestShopItem*2+40}} (Currently set to {config["shopItems"][item]})")

print("'refresh': Refresh potatbotat cooldowns if they are wrong\n")
print("Manual changes to config requires restart to update\n")


logger.debug("Started bot")

while True:
    try:
        if executions > 20:
            logger.warning("Hit client-side ratelimit")
            print(f"{strftime("%H:%M:%S")} Hit client-side ratelimit, paused for 1h - commands will not work during this time")

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
            print("Refreshed cooldowns\n")

            executedCommand = False

            if potatoes >= rankCost:
                if rank == 6:
                    ok, response = api.send("prestige")
                    print(response)

                else:
                    ok, response = api.send("rankup")
                    print(response)
                
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

                print(response)


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
            print(response)
            sleep(5)

            ok, quiz = api.potatSend("quiz", cdRetries=3)

            if not ok:
                logger.warning(f"Failed to get quiz: {quiz}")
                print(f"Failed to get quiz: {quiz}")
                continue


            # Example response:󠀀 ⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: <quiz>
            print(f"{quiz=}")
            answer = quizes.get(quiz, None)

            if answer is None:
                logger.warning(f"No quiz anser found for quiz: {quiz}")
                print(f"No quiz answer found for quiz: {quiz}")
                continue
            

            print(f"Found quiz answer: {answer}")

            sleep(5) # small cooldown to be safe
            pk, response = api.twitchSend(f"{answer}", prefix=False)
            print(response)


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
        print(f"Stopped bot: {e}")
        sleep(3000000)


    except Exception as e:
        executions += 1
        print(f"ERROR: {e}")

        logger.error(f"Caught exception in main", exc_info=e)

        sleep(5)

import json
import threading
import queue

from traceback import format_exc
from time import time, sleep, strftime

import api
from config import loopDelay, executedCommand, boughtShopItem, executions, allFarmingCommands, allShopItems
from data import getConfig, updateConfig, log
from priceUtils import rankPrice


with open("quizes.json", "r") as file:
    quizes = json.loads(file.read())

config = getConfig()

potatData = {}
cooldowns = []

uInputs = queue.Queue()

def inputs():
    while True:
        uInput = input().lower()
        uInputs.put(uInput)

        if uInput == "s":
            break
        elif uInput in allFarmingCommands:
            config["farmingCommands"][uInput] = bool(config["farmingCommands"][uInput] is False)
            api.farmingCommands = config["farmingCommands"]
            updateConfig(config)
            print(f"Toggled command '{uInput}', set to {config["farmingCommands"][uInput]}")

        elif uInput in allShopItems:
            config["shopItems"][uInput] = bool(config["shopItems"][uInput] is False)
            api.shopItems = config["shopItems"]
            updateConfig(config)
            print(f"Toggled auto buying for '{uInput}', set to {config["shopItems"][uInput]}")

        elif "twitch" in uInput:
            api.usePotatApi = False
            config["usePotatApi"] = False
            updateConfig(config)
            print("Switched to twitch messages")

        elif uInput == "potat" or uInput == "potatbotat":
            api.usePotatApi = True
            config["usePotatApi"] = True
            updateConfig(config)
            print("Switched to potatbotat api")

        elif uInput == "refresh":
            print("Refreshing cooldowns...")

        else:
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


while True:
    try:
        if executions > 20:
            api.log("TOO MANY EXECUTIONS")
            print(f"{strftime("%H:%M:%S")} Errored / executed too many commands in a short period of time, paused for 1h - commands will not work during this time")
            executions = 0
            sleep(3600)


        if not uInputs.empty():
            uInput = uInputs.get()
            if uInput == "s":
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
            print("Refreshed cooldowns\n")

            executedCommand = False

            if potatoes >= rankCost:
                if rank == 6:
                    print(api.send("prestige"))
                else:
                    print(api.send("rankup"))
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


                print(api.send(cooldown))


                if cooldown == "cdr":
                    if shopCooldowns.get("shop-cdr", time()+10) < time():
                        if boughtShopItem:
                            sleep(5) 
                        
                        boughtShopItem = api.buyItem(item="cdr", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem

                sleep(1)
                continue


            # first execute the quiz in the targetted twitch chat
            # to not send "🥳 Thats right! Congratulations on getting the right answer, heres # potatoes!" in your own chat
            print(api.twitchSend("quiz"))
            sleep(5)
            quiz = api.potatSend("quiz", cdRetries=3)


            # Example response:󠀀 ⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: <quiz>
            print(f"{quiz=}")
            answer = quizes.get(quiz, None)

            if answer is None:
                log(f"FAILED QUIZ: {quiz=}")
                print("FAILED QUIZ")
                continue
            

            print(f"{answer=}")
            sleep(5) # small cooldown to be safe
            print(api.twitchSend(f"{answer}", prefix=False))

            if shopCooldowns.get("shop-quiz", time()+10) < time():
                if boughtShopItem:
                    sleep(5)
                
                boughtShopItem = api.buyItem(item="quiz", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem

            executions += 2
            continue

        executions -= loopDelay/10 if loopDelay < 90 else 0.9
        sleep(loopDelay)



    except api.stopBot as e:
        log(f"STOPPED BOT: {e}")
        print(f"stopped bot: {e}")
        sleep(3000000)

    except IndexError as e:
        executions += 1
        print(f"ERROR: {e}")
        log(f"INDEX ERROR : {type(e).__name__} {e}")
        log(format_exc())
        sleep(5)

    except Exception as e:
        executions += 1
        print(f"ERROR: {e}")
        log(f"EXCEPTION ERROR : {type(e).__name__} {e}")
        log(format_exc())
        sleep(5)
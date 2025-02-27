import api
from config import loopDelay, rankupCosts, executedCommand, boughtShopItem, executions, allFarmingCommands, allShopItems
from time import time, sleep, strftime
from traceback import format_exc
import json
import threading
import queue
from data import getConfig, updateConfig, log

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
            rankupCost = rankupCosts[rank]
            if rank == 6:
                rankupCost += 20000*potatoData["prestige"]

            cooldowns = potatoData["cooldowns"]
            print("Refreshed cooldowns\n")

            executedCommand = False

            if potatoes >= rankupCost:
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
                        print(api.send("shop fertilizer"))
                        sleep(5) # shop cooldown
                        boughtShopItem = True
                    if shopCooldowns.get("shop-guard", time()+10) < time():
                        print(api.send("shop guard"))
                        sleep(5) # shop cooldown
                        boughtShopItem = True

                print(api.send(cooldown))

                if cooldown == "cdr":
                    if shopCooldowns.get("shop-cdr", time()+10) < time():
                        print(api.send("shop cdr"))
                        boughtShopItem = True

                sleep(1)
                continue

            print(api.twitchSend("#quiz")) # first execute the quiz in the targetted twitch chat
            sleep(5)
            quiz = api.potatSend("#quiz")  # to not send "🥳 Thats right! Congratulations on getting the right answer, heres # potatoes!" in your own chat

            # Example response:󠀀 ⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: A potato farmer is planting potatoes in rows, and each row contains 20 potatoes. If the farmer has 12 rows, how many potatoes are planted in total? 
            print(f"{quiz=}")
            answer = quizes.get(quiz, None)
            if answer is None:
                log(f"FAILED QUIZ: {quiz=}")
                print("FAILED QUIZ")
                continue
            
            print(f"{answer=}")
            sleep(5)
            print(api.twitchSend(f"{answer}")) # answering with just the answer works and doesn't have a cooldown, but still add a cooldown incase it changes

            if shopCooldowns.get("shop-quiz", time()+10) < time():
                print(api.send("shop quiz"))
                sleep(5) # shop cooldown
                boughtShopItem = True

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
        log(f"INDEX ERROR : {type(e).__name__} {e}")
        log(format_exc())
        sleep(5)
    except Exception as e:
        executions += 1
        log(f"EXCEPTION ERROR : {type(e).__name__} {e}")
        log(format_exc())
        sleep(5)
import api
from config import loopDelay, rankupCosts, executedCommand, executions, allFarmingCommands
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
for command in allFarmingCommands:
    print(f"'{command}': Toggle auto farming for {command}")
print("'refresh': Refresh potatbotat cooldowns if they are wrong\n")
print("Manual changes to config requires restart to update\n")

while True:
    try:
        if not uInputs.empty():
            uInput = uInputs.get()
            if uInput == "s":
                break

            elif uInput in allFarmingCommands:
                executedCommand = True

            elif "refresh" in uInput:
                executedCommand = True


        if executedCommand:
            sleep(1) # let the db update
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
                print(api.send(cooldown))
                continue

            quiz = api.potatSend("#quiz")
            print(quiz)
            if not quiz.startswith("Executed command:"):
                continue

            quiz = quiz.split("': ", 1)[1].strip()
            answer = quizes[quiz]
            print(f"{answer=}")
            sleep(6) # answer has a 5 second cooldown after quiz + 1s margin
            # force potat api, because commands get executed in your own chat, only way to read quiz
            print(api.potatSend(f"#a {answer}"))
            continue

        if executions > 15:
            api.log("TOO MANY EXECUTIONS")
            print(f"{strftime("%H:%M:%S")} Executed too many commands in a short period of time, paused for 1h")
            sleep(3600)

        executions -= loopDelay/10 if loopDelay < 90 else 0.9
        sleep(loopDelay)

    except api.stopBot as e:
        log(f"STOPPED BOT: {e}")
        print(f"stopped bot: {e}")
        sleep(3000000)
    except IndexError as e:
        log(f"INDEX ERROR : {type(e).__name__} {e}")
        log(format_exc())
        sleep(5)
    except Exception as e:
        log(f"EXCEPTION ERROR : {type(e).__name__} {e}")
        log(format_exc())
        sleep(5)
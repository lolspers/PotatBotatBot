import os

from datetime import datetime
from colorama import Fore, Style, Back
from time import time, sleep, strftime

import exceptions
import api.cooldowns
import api.execute
from logger import logger, cprint, clprint, tprint, killProgram
from utils import rankPrice, relative, farmingCommands, shopItems
from inputs import Inputs
from prestige import updatePrestigeStats



loopDelay: int = 1
executions: float = 0

executedCommand: bool = True
boughtShopItem: bool = True


inputs = Inputs()

logger.debug("Started bot")

while True:
    try:
        if executions > 20:
            logger.warning("Hit client-side ratelimit")
            cprint(f"({strftime("%H:%M:%S")}) Hit client-side ratelimit, paused for 1h until {datetime.fromtimestamp(time() + 3600).strftime("%H:%M:%S")} - commands will not work during this time", fore=Fore.RED)

            executions = 0
            sleep(3600)

            logger.debug("Resumed bot")
            cprint("Resumed", fore=Fore.CYAN, style=Style.DIM)


        if not inputs.queue.empty():
            uInput = inputs.queue.get()
            if uInput == "s":
                logger.info("Stopped bot by users request")
                break

            elif uInput in farmingCommands:
                executedCommand = True

            elif uInput in shopItems:
                boughtShopItem = True

            elif uInput in ["refetch", "refresh"]:
                executedCommand = True
                boughtShopItem = True


        if boughtShopItem:
            executions += 2
            shopCooldowns = api.cooldowns.shopCooldowns()
            boughtShopItem = False

            print()
            tprint("Refreshed shop cooldowns")

            for item, cooldown in shopCooldowns.items():
                readyIn = relative(cooldown - time())

                cprint(f"{item}: {readyIn}", style=Style.DIM if "in" in readyIn else None, time=False)

            print()


        if executedCommand:
            executions += 1
            potatoData = api.cooldowns.normalCooldowns()

            potatoes: int = potatoData["potatoes"]
            rank: int = potatoData["rank"]
            prestige: int = potatoData["prestige"]

            rankCost: int = rankPrice(prestige, rank)

            cooldowns: dict[str, int] = potatoData["cooldowns"]

            print()
            tprint("Refreshed cooldowns")

            for command, cooldown in cooldowns.items():
                readyIn = relative(cooldown - time())

                cprint(f"{command}: {readyIn}", style=Style.DIM if "in" in readyIn else None, time=False)

            print()
            

            executedCommand = False

            if potatoes >= rankCost:
                if rank == 6:
                    ok, response = api.execute.send("prestige")

                    if not ok:
                        clprint("Failed to prestige", response, style=[Style.BRIGHT], globalFore=Fore.RED)

                    else:
                        clprint("Successfully prestiged:", response, style=[Style.BRIGHT], globalFore=Fore.YELLOW)

                        sleep(1)

                        result = updatePrestigeStats()

                        if result.get("error"):
                            clprint("Failed to update prestige stats:", result["error"], style=[Style.BRIGHT], globalFore=Fore.RED)

                        else:
                            cprint("Updated prestige stats", fore=Fore.GREEN, style=Style.DIM)
                        

                else:
                    ok, response = api.execute.send("rankup")

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
                        boughtShopItem = api.execute.buyItem(item="fertilizer", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem
                    
                    if shopCooldowns.get("shop-guard", time()+10) < time():
                        if boughtShopItem:
                            sleep(5) 
                        
                        boughtShopItem = api.execute.buyItem(item="guard", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem


                ok, response = api.execute.send(cooldown)

                if not ok:
                    clprint("Failed to execute command:", response, style=[Style.BRIGHT], globalFore=Fore.RED)

                else:
                    clprint("Executed command:", response, style=[None, Style.DIM])


                if cooldown == "cdr":
                    if shopCooldowns.get("shop-cdr", time()+10) < time():
                        if boughtShopItem:
                            sleep(5) 
                        
                        boughtShopItem = api.execute.buyItem(item="cdr", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem

                sleep(1)
                continue

            
            else:
                api.execute.executeQuiz()

                if shopCooldowns.get("shop-quiz", time()+10) < time():
                    if boughtShopItem:
                        sleep(5)
                    
                    boughtShopItem = api.execute.buyItem(item="quiz", rank=rank, potatoes=potatoes) if not boughtShopItem else boughtShopItem

                executions += 2
                continue


        executions -= loopDelay/10 if loopDelay < 90 else 0.9

        sleep(loopDelay)



    except exceptions.StopBot as e:
        logger.critical(f"Stopped bot: {e}")
        print("\n")
        clprint("Stopped bot:", str(e), style=[Style.BRIGHT, None], globalFore=Fore.MAGENTA)

        killProgram()

    
    except KeyboardInterrupt as e:
        os._exit(1)


    except Exception as e:
        executions += 1
        clprint(f"{type(e).__name__}:", str(e), style=[Style.BRIGHT], globalFore=Fore.RED)

        logger.error(f"Caught exception in main", exc_info=e)

        sleep(5)


killProgram()
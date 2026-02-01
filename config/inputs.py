from __future__ import annotations
from typing import TYPE_CHECKING
from colorama import Fore, Style, Back
from threading import Thread
from queue import Queue

from . import config
from .config import defaultFarmingCommands, defaultShopItems
from logger import logger, cprint, clprint
from prestige import updatePrestigeStats

import logger as loggerModule


if TYPE_CHECKING:
    from classes.user import User


def canEnableTwitch() -> bool:
    if not config.clientSecret or not config.clientId:
        return False
    
    if config.authCode:
        return True
    
    if not config.twitchToken or not config.refreshToken:
        return False

    return True


class Inputs:
    def __init__(self, user: User) -> None:
        self.user: User = user
        self.queue = Queue()
        self.thread = Thread(target=self.loop, daemon=True)
        self.thread.start()
        self.active: bool = False

        self.printCommands()



    def printCommands(self) -> None:
        potatCmdMsg: str = "Toggle auto farming for"
        potatShopMsg: str = "Toggle auto buying for"
        maxCmdLength: int = max(len(max(defaultFarmingCommands, key=len)), len(max(defaultShopItems, key=len)))
        spaceMargin = maxCmdLength * 2 + len(potatCmdMsg)

        lines: list[dict[str, str] | str] = [
            "Type at any time to execute a command",
            "Available commands:",
            {
                "s": "Stop the bot and close the program",
                "potat": "Switch to using potatbotat api",
                "twitch": "Switch to using twitch api",
            },
            "",
            {
                command: f"{f"{potatCmdMsg} {command}": <{spaceMargin-len(command)+2}} (Currently set to {config.farmingCommands[command]})"
                for command in list(defaultFarmingCommands.keys())
            },
            {
                item: f"{f"{potatShopMsg} {item}": <{spaceMargin-len(item)+2}} (Currently set to {config.shopItems[item]})"
                for item in list(defaultShopItems.keys())
            },
            "",
            {
                "refetch": "Force refetching of potatbotat cooldowns",
                "stats": "Manually update prestige stats for the current prestige, if they do not exist yet",
                "color": "Toggle printing in color",
                "time": "Toggle printing time"
            },
            "Manual changes to config.json require a restart to take effect.",
            ""
        ]

        for line in lines:
            if isinstance(line, str):
                cprint(line, time=False)
            elif isinstance(line, dict):
                for command, description in line.items():
                    clprint(f"'{command}'", description, style=[None, Style.DIM], time=False)



    def loop(self) -> None:
        logger.debug("Started input loop")
        self.active = True

        while self.active:
            try:
                uInput = input().lower()
                if loggerModule.killedProgram:
                    break

                self.queue.put(uInput)

                logger.debug(f"Received user input: {uInput}")

                if uInput == "s":
                    logger.info("Stopped by users request")
                    break


                elif uInput in defaultFarmingCommands:
                    enable = not config.farmingCommands[uInput]
                    config.farmingCommands[uInput] = enable
                    cprint(f"{"Enabled" if enable else "Disabled"} command '{uInput}'", fore=Fore.CYAN)
                    self.user.setData()


                elif uInput in defaultShopItems:
                    enable = not config.shopItems[uInput]
                    config.shopItems[uInput] = enable
                    cprint(f"{"Enabled" if enable else "Disabled"} auto buying for '{uInput}'", fore=Fore.CYAN)
                    self.user.setShopCooldowns()


                elif uInput in ["twitch", "twitchapi"]:
                    if not canEnableTwitch():
                        cprint(f"Failed to enable twitch api: one or more credentials in config.json are not set", fore=Fore.RED)
                        continue

                    config.usePotat = False
                    cprint("Switched to twitch messages", fore=Fore.CYAN)


                elif uInput in ["potat", "potatapi", "potatbotat"]:
                    config.usePotat = True
                    cprint("Switched to potat api", fore=Fore.CYAN)


                elif uInput in ["refresh", "refetch"]:
                    cprint("Refreshing cooldowns...", fore=Fore.CYAN)
                    self.user.setData()
                    self.user.setShopCooldowns()


                elif uInput == "stats":
                    self.user.setData()
                    result = updatePrestigeStats(self.user)

                    if result.get("error"):
                        clprint("Failed to update prestige stats:", result["error"], style=[Style.BRIGHT], globalFore=Fore.RED)
                    else:
                        cprint("Updated prestige stats", fore=Fore.GREEN, style=Style.DIM)


                elif uInput == "color":
                    enable = not config.printColor
                    config.printColor = enable
                    cprint(f"{"Enabled" if enable else "Disabled"} printing in color", fore=Fore.CYAN)


                elif uInput == "time":
                    enable = not config.printTime
                    config.printTime = enable
                    cprint(f"{"Enabled" if enable else "Disabled"} printing time", fore=Fore.CYAN)


                else:
                    logger.debug(f"Invalid user command: {uInput}")
                    cprint(f"Invalid command: '{uInput}'", fore=Fore.YELLOW)
                    continue


                config.dumpConfig()


            except EOFError:
                break
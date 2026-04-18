from __future__ import annotations

from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING

from colorama import Fore, Style

import globals as g
from api import twitch
from prestige import updatePrestigeStats

from .config import defaultFarmingCommands, defaultShopItems

if TYPE_CHECKING:
    from classes.user import User


def canEnableTwitch() -> bool:
    if not g.config.clientSecret or not g.config.clientId:
        return False

    if g.config.authCode:
        return True

    return bool(g.config.twitchToken and g.config.refreshToken)


class Inputs:
    def __init__(self, user: User) -> None:
        self.user: User = user
        self.queue = Queue()
        self.active: bool = False
        self.thread = Thread(target=self.loop, daemon=True)
        self.thread.start()

        self.printCommands()



    def printCommands(self) -> None:
        potatCmdMsg: str = "Toggle auto farming for"
        potatShopMsg: str = "Toggle auto buying for"
        maxCmdLength: int = max(len(max(defaultFarmingCommands, key=len)),
                                len(max(defaultShopItems, key=len)))
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
                command: f"{f"{potatCmdMsg} {command}": <{spaceMargin-len(command)+2}} " \
                            f"(Currently set to {g.config.farmingCommands[command]})"
                for command in list(defaultFarmingCommands.keys())
            },
            {
                item: f"{f"{potatShopMsg} {item}": <{spaceMargin-len(item)+2}} " \
                        f"(Currently set to {g.config.shopItems[item]})"
                for item in list(defaultShopItems.keys())
            },
            "",
            {
                "refetch": "Force refetching of potatbotat cooldowns",
                "stats": "Manually update prestige stats for the current prestige, " \
                            "if they do not exist yet",
                "color": "Toggle printing in color",
                "time": "Toggle printing time",
                "emoji": "Toggle printing emojis",
            },
            "Manual changes to g.config.json require a restart to take effect.",
            "",
        ]

        for line in lines:
            if isinstance(line, str):
                print(line)
            elif isinstance(line, dict):
                for command, description in line.items():
                    g.logger.info(f"'{command}': %s{description}",
                                  Style.DIM,
                                  extra={"print": True, "write": False, "time": False})



    def loop(self) -> None:
        g.logger.debug("Started input loop")
        self.active = True

        while self.active:
            try:
                uInput = input().lower()

                self.queue.put(uInput)

                g.logger.debug(f"Received user input: {uInput}")

                if uInput == "s":
                    g.logger.info("Stopped by users request",
                                  extra={"print": True})
                    break


                if uInput in defaultFarmingCommands:
                    enable = not g.config.farmingCommands[uInput]
                    g.config.farmingCommands[uInput] = enable
                    g.logger.info(f"{"Enabled" if enable else "Disabled"} command '{uInput}'",
                                  extra={"color": Fore.CYAN, "print": True})
                    self.user.setCooldowns(shop=False)


                elif uInput in defaultShopItems:
                    enable = not g.config.shopItems[uInput]
                    g.config.shopItems[uInput] = enable
                    g.logger.info(
                        f"{"Enabled" if enable else "Disabled"} auto buying for '{uInput}'",
                        extra={"color": Fore.CYAN, "print": True})
                    self.user.setCooldowns()


                elif uInput in ["twitch", "twitchapi"]:
                    if not canEnableTwitch():
                        g.logger.error("Failed to enable twitch api: " \
                               "one or more credentials in g.config.json are not set",
                                extra={"color": Fore.CYAN, "print": True})
                        continue

                    if g.config.authCode:
                        twitch.generateToken()

                    g.config.usePotat = False
                    g.logger.info("Switched to twitch messages")


                elif uInput in ["potat", "potatapi", "potatbotat"]:
                    g.config.usePotat = True
                    g.logger.info("Switched to potat api",
                                  extra={"color": Fore.CYAN, "print": True})


                elif uInput in ["refresh", "refetch"]:
                    g.logger.info("Refreshing cooldowns...",
                                  extra={"color": Fore.CYAN, "print": True})
                    self.user.setCooldowns()


                elif uInput == "stats":
                    self.user.setData()
                    result = updatePrestigeStats(self.user)

                    if result.get("error"):
                        g.logger.error("Failed to update prestige stats: %s%s",
                                       Style.NORMAL, result["error"],
                                       extra={"color": Style.BRIGHT, "print": True})
                    else:
                        g.logger.info("Updated prestige stats",
                                      extra={"color": Fore.GREEN + Style.DIM, "print": True})


                elif uInput == "color":
                    enable = not g.config.printColor
                    g.config.printColor = enable
                    g.logger.info(f"{"Enabled" if enable else "Disabled"} printing in color",
                                  extra={"color": Fore.CYAN, "print": True})


                elif uInput == "time":
                    enable = not g.config.printTime
                    g.config.printTime = enable
                    g.logger.info(f"{"Enabled" if enable else "Disabled"} printing time",
                                  extra={"color": Fore.CYAN, "print": True})


                elif uInput in ["emoji", "emojis"]:
                    enable = not g.config.printEmojis
                    g.config.printEmojis = enable
                    g.logger.info(f"{"Enabled" if enable else "Disabled"} printing emojis",
                                  extra={"color": Fore.CYAN, "print": True})


                else:
                    g.logger.info(f"Invalid command: '{uInput}'",
                                  extra={"color": Fore.YELLOW, "print": True})
                    continue


                g.config.dumpConfig()


            except EOFError:
                break

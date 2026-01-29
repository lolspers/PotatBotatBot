from colorama import Fore, Style, Back
from threading import Thread
from queue import Queue

from config import config
from logger import logger, cprint, clprint
from prestige import updatePrestigeStats
from utils import farmingCommands, shopItems



class Inputs:
    def __init__(self) -> None:
        self.queue = Queue()
        self.thread = Thread(target=self.loop, daemon=True)
        self.thread.start()
        self.active: bool = False

        self.printCommands()



    def printCommands(self) -> None:
        potatCmdMsg: str = "Toggle auto farming/buying for"
        maxCmdLength: int = max(len(max(shopItems, key=len)), len(max(shopItems, key=len)))
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
                command: f"{f"{potatCmdMsg} {command}": <{spaceMargin-len(command)+2}} (Currently set to {config.isEnabled(command)})"
                for command in farmingCommands + shopItems
            },
            "",
            {
                "refetch": "Force refetching of potatbotat cooldowns",
                "stats": "Manually update prestige stats for the current prestige, if they do not exist yet",
                "color": "Toggle printing in color",
                "time": "Toggle printing time"
            },
            "Manual changes to config.json require a restart to take effect."
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
                self.queue.put(uInput)

                logger.debug(f"Received user input: {uInput}")

                if uInput == "s":
                    logger.info("Stopped by users request")
                    break

                elif uInput in farmingCommands:
                    enabled = config.toggleCommand(uInput)
                    cprint(f"{"Enabled" if enabled else "Disabled"} command '{uInput}'", fore=Fore.CYAN)

                elif uInput in shopItems:
                    enabled = config.toggleCommand(uInput)
                    cprint(f"{"Enabled" if enabled else "Disabled"} auto buying for '{uInput}'", fore=Fore.CYAN)

                elif uInput in ["twitch", "twitchapi"]:
                    enabled = config.enableTwitch()

                    if not enabled:
                        cprint("Failed to switch to twitch api", fore=Fore.RED)
                    else:
                        cprint("Switched to twitch messages", fore=Fore.CYAN)

                elif uInput in ["potat", "potatapi", "potatbotat"]:
                    enabled = config.enablePotat()

                    if not enabled:
                        cprint("Cannot enable potat api: potatToken is not set in the config!", fore=Fore.MAGENTA)
                    else:
                        cprint("Switched to potat api", fore=Fore.CYAN)

                elif uInput in ["refresh", "refetch"]:
                    cprint("Refreshing cooldowns...", fore=Fore.CYAN)

                elif uInput == "stats":
                    result = updatePrestigeStats()

                    if result.get("error"):
                        clprint("Failed to update prestige stats:", result["error"], style=[Style.BRIGHT], globalFore=Fore.RED)
                    else:
                        cprint("Updated prestige stats", fore=Fore.GREEN, style=Style.DIM)

                elif uInput == "color":
                    enabled = config.toggleColoredPrinting()
                    cprint(f"{"Enabled" if enabled else "Disabled"} printing in color", fore=Fore.CYAN)

                elif uInput == "time":
                    enabled = config.toggleTimePrinting()
                    cprint(f"{"Enabled" if enabled else "Disabled"} printing time", fore=Fore.CYAN)

                else:
                    logger.debug(f"Invalid user command: {uInput}")
                    cprint(f"Invalid command: '{uInput}'", fore=Fore.YELLOW)

                print()


            except EOFError:
                break
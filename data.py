import json

from colorama import Fore, Style
from os import _exit

from logger import logger


def getConfig():
    logger.debug("Getting config...")

    try:
        with open("config.json", "r") as file:
            return json.loads(file.read())
        
    except FileNotFoundError:
        logger.warning("config.json file was not found")
        input(Style.BRIGHT + Fore.MAGENTA + "Please set up config.json or run setup.py before starting the bot")
        _exit(1)


def updateConfig(data):
    logger.debug(f"Updating config: {data}")

    with open("config.json", "w") as file:
        json.dump(data, file, indent=4)
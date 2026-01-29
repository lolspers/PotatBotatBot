from time import time

from . import potat
from config import config
from logger import logger


unitToSeconds = {
    "s": 1, 
    "m": 60, 
    "h": 3600, 
    "d": 86400
}



def normalCooldowns() -> dict:
    data = potat.getUser(config.username)

    potatoData = data["potatoes"]

    potatoes = potatoData["count"]
    rank = potatoData["rank"]
    prestige = potatoData["prestige"]

    cooldowns = {
        "potato": potatoData["potato"]["readyAt"],
        "steal": potatoData["steal"]["readyAt"],
        "trample": potatoData["trample"]["readyAt"],
        "cdr": potatoData["cdr"]["readyAt"],
        "quiz": potatoData["quiz"]["readyAt"]
    }
    filteredCooldowns = {}

    for command, cooldown in cooldowns.items():
        if not config.isEnabled(command):
            continue

        if cooldown is None:
            filteredCooldowns[command] = 0

        else:
            filteredCooldowns[command] = int(cooldown/1000 + 1)
    
    
    logger.debug(f"Updated cooldowns: {filteredCooldowns}")

    return {"potatoes": potatoes, "rank": rank, "prestige": prestige, "cooldowns": filteredCooldowns}



def shopCooldowns() -> dict[str, float]:
    ok, res = potat.execute("status")

    if not ok:
        logger.error(f"Failed to get shop cooldowns: {res=}")
        raise Exception(f"Failed to get shop cooldowns: {res.get("text", res["error"])}")
    

    rawCooldowns: str = res["text"].split(": ", 2)[2].replace("\u2705", "0s").lower()

    potatCooldowns = {
        cooldown.split(": ", 1)[0]: cooldown.split(": ", 1)[1]
        for cooldown in rawCooldowns.split(" ● ")
        if cooldown.startswith("shop-")
    }
    

    shopCooldowns = {}

    for command in potatCooldowns:
        if not config.isEnabled(command):
            continue

        cooldowns = potatCooldowns[command].split(" and ")
        readyIn = time()

        for cooldown in cooldowns:
            if not "s" in cooldown:
                readyIn += 60 # status rounds down

            readyIn += int(cooldown[:-1]) * unitToSeconds[cooldown[-1]]

        shopCooldowns.update({command: readyIn})


    logger.debug(f"New shop cooldowns: {shopCooldowns}")

    return shopCooldowns
import os
import json

from datetime import datetime
from time import time

from api.potat import getPotatUser
from config import config
from logger import logger


basePath = "prestige/"
statsPath = basePath + "prestigeStats.json"



def getPrestigeStats() -> dict[str, dict[str, dict[str, int]]]:
    try:
        with open(statsPath, "r") as file:
            data = file.read()

        return json.loads(data)
        

    except json.JSONDecodeError as e:
        path = basePath + "decodeError"

        if not os.path.isdir(path):
            os.mkdir(path)


        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        newPath = path + f"/{date}.txt"

        with open(newPath, "w") as file:
            file.write(data)


        logger.error(f"Prestige: JSONDecodeError, moved data to '{newPath}'")


    except FileNotFoundError as e:
        logger.info("Prestige: FileNotFoundError, created prestigeStats.json")

        with open(statsPath, "w"):
            pass


    return {}



def updatePrestigeStats() -> dict:
    userdata = getPotatUser(config.username)

    potatdata = userdata.get("potatoes")

    if not potatdata:
        logger.warning(f"Prestige: Tried to update prestige stats, but user '{config.username}' has never farmed before")
        return {"error": "User has never farmed"}


    prestige = str(potatdata["prestige"])

    potato = potatdata["potato"]
    steal = potatdata["steal"]
    trample = potatdata["trample"]
    quiz = potatdata["quiz"]
    gamble = potatdata["gamble"]
    duel = potatdata["duel"]


    prestigeData = {
        "general": {
            "prestigedAt": int(time())
        },
        "potato": {
            "usage": potato["usage"]
        },
        "steal": {
            "usage": steal["theftCount"],
            "stolenFrom": steal["stolenCount"]
        },
        "trample": {
            "usage": trample["trampleCount"],
            "trampled": trample["trampledCount"]
        },
        "quiz": {
            "attempted": quiz["attempted"],
            "completed": quiz["completed"]
        },
        "gamble": {
            "wins": gamble["winCount"],
            "losses": gamble["loseCount"],
            "totalWon": gamble["totalWins"],
            "totalLost": gamble["totalLosses"]
        },
        "duel": {
            "wins": duel["winCount"],
            "losses": duel["loseCount"],
            "totalWon": duel["totalWins"],
            "totalLost": abs(duel["totalLosses"]),
            "caughtLosses": duel["caughtLosses"]
        }
    }


    allStats = getPrestigeStats()

    if allStats.get(prestige):
        logger.warning(f"Prestige: Tried to update prestige stats, but data for prestige {prestige} already exists\n new data: {prestigeData}")
        return {"error": f"Data for prestige {prestige} already exists"}
    

    allStats.update({prestige: prestigeData})

    with open(statsPath, "w") as file:
        json.dump(allStats, file, indent=4)


    return {"message": f"Added prestige data for prestige {prestige}"}
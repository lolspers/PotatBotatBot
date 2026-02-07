from __future__ import annotations
from typing import TYPE_CHECKING

import os
import json

from datetime import datetime
from time import time

from logger import logger

if TYPE_CHECKING:
    from classes.user import User


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



def updatePrestigeStats(user: User) -> dict:
    prestige = str(user.prestige)
    commands = user.commands


    prestigeData = {
        "general": {
            "prestigedAt": int(time())
        },
        "potato": {
            "usage": commands.potato.usage
        },
        "steal": {
            "usage": commands.steal.usage,
            "stolenFrom": commands.steal.stolenCount
        },
        "trample": {
            "usage": commands.trample.usage,
            "trampled": commands.trample.trampledCount
        },
        "quiz": {
            "attempted": commands.quiz.attempted,
            "completed": commands.quiz.completed
        },
        "gamble": {
            "wins": commands.gamble.wins,
            "losses": commands.gamble.losses,
            "totalWon": commands.gamble.earned,
            "totalLost": commands.gamble.lost
        },
        "duel": {
            "wins": commands.duel.wins,
            "losses": commands.duel.losses,
            "totalWon": commands.duel.earned,
            "totalLost": commands.duel.lost,
            "caughtLosses": commands.duel.caughtLosses
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
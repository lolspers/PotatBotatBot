from __future__ import annotations

import json
import os
from datetime import datetime
from time import time
from typing import TYPE_CHECKING

import globals as g

if TYPE_CHECKING:
    from classes.user import User


basePath = "prestige/"
statsPath = basePath + "prestigeStats.json"



def getPrestigeStats() -> dict[str, dict[str, dict[str, int]]]:
    try:
        with open(statsPath) as file:
            data = file.read()

    except FileNotFoundError:
        g.logger.info("Prestige: FileNotFoundError, created prestigeStats.json")

        with open(statsPath, "w"):
            pass

        return {}

    try:
        return json.loads(data)

    except json.JSONDecodeError:
        path = basePath + "decodeError"

        if not os.path.isdir(path):
            os.mkdir(path)


        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        newPath = path + f"/{date}.txt"

        with open(newPath, "w") as file:
            file.write(data)


        g.logger.error(f"Prestige: JSONDecodeError, moved data to '{newPath}'")

        return {}



def updatePrestigeStats(user: User) -> dict:
    prestige = str(user.prestige)
    commands = user.commands


    prestigeData = {
        "general": {
            "prestigedAt": int(time()),
        },
        "potato": {
            "usage": commands.potato.usage,
        },
        "steal": {
            "usage": commands.steal.usage,
            "stolenFrom": commands.steal.stolenCount,
        },
        "trample": {
            "usage": commands.trample.usage,
            "trampled": commands.trample.trampledCount,
        },
        "quiz": {
            "attempted": commands.quiz.attempted,
            "completed": commands.quiz.completed,
        },
        "gamble": {
            "wins": commands.gamble.wins,
            "losses": commands.gamble.losses,
            "totalWon": commands.gamble.earned,
            "totalLost": commands.gamble.lost,
        },
        "duel": {
            "wins": commands.duel.wins,
            "losses": commands.duel.losses,
            "totalWon": commands.duel.earned,
            "totalLost": commands.duel.lost,
            "caughtLosses": commands.duel.caughtLosses,
        },
    }


    allStats = getPrestigeStats()

    if allStats.get(prestige):
        g.logger.warning("Prestige: Tried to update prestige stats, " \
                       f"but data for prestige {prestige} already exists\nnew data: {prestigeData}",
                       extra={"print": False})
        return {"error": f"Data for prestige {prestige} already exists"}


    allStats.update({prestige: prestigeData})

    with open(statsPath, "w") as file:
        json.dump(allStats, file, indent=4)


    return {"message": f"Added prestige data for prestige {prestige}"}

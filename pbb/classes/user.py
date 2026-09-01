import json
import os
from time import sleep, time

from colorama import Fore

import pbb.globals as g
import pbb.stats.stats as stats
from pbb.api import potat, twitch
from pbb.classes.channel import PotatChannel
from pbb.classes.commands import Cdr, Commands, Prestige, Quiz, Rankup
from pbb.classes.userdata import UserData
from pbb.config.inputs import canEnableTwitch
from pbb.exceptions import StopBot
from pbb.prestige import updatePrestigeStats
from pbb.utils import relative, shortUnitToSeconds

quizesPath = os.path.join(g.packageDir, "quizes.json")
with open(quizesPath) as file:
    quizes: dict[str, str] = json.loads(file.read())



class User(UserData):
    def __init__(self) -> None:
        UserData.channel = PotatChannel(g.config.channelId, joinRequired=True)
        UserData.potatUser, UserData.potatUid = potat.getSelf()

        if not g.config.usePotat or (g.config.usePotat and g.config.oppositePlatform):
            if not canEnableTwitch():
                raise StopBot("Tried to use twitch api, " \
                              "but one or more twitch credentials are not set")

            if g.config.authCode:
                twitch.generateToken()

            UserData.twitchUser, UserData.twitchUid = twitch.getSelf()
            UserData.channel.setChannelData()

        else:
            UserData.twitchUser, UserData.twitchUid = ("", "")

        self.commands: Commands = Commands()
        self.executions: float = 0



    def getApiData(self) -> dict:
        ok, data = potat.getUser(self.username)

        if not ok:
            if data.get("status") == 404:
                raise StopBot(f"Potat user '{self.username}' not found")

            g.logger.critical("Failed to get user stats", extra={"data": data})
            raise Exception("Failed to get potat user data: " \
                            f"{data.get("error", data)} ({data.get("status")})")

        d = data.get("potatoes")

        if not d:
            g.logger.critical(f"No potato data found for user '{self.username}'")
            raise StopBot(f"No potato data found for user '{self.username}'")

        return d


    def getPotatoCount(self) -> int:
        data = self.getApiData()
        return data["count"]


    def setData(self, balanceCommand: str = "rank", responseText: str = "") -> None:
        g.logger.debug("Setting user data")
        hadPlayer = bool(stats.playerInfo["username"])
        balanceBeforeRefresh = int(stats.playerInfo["potatoes"])

        data = self.getApiData()

        def getCmdCd(data: dict) -> int:
            return data["readyAt"] // 1000 if data["readyAt"] else 0

        self.joinedAt: str = data["joinedAt"]
        UserData.prestige = data["prestige"]
        UserData.rank = data["rank"]
        UserData.potatoes = data["count"]
        UserData.taxMultiplier = data["taxMultiplier"]
        self.verbose: bool = data["verbose"]

        self.commands.potato.readyAt = getCmdCd(data["potato"])
        self.commands.potato.ready = data["potato"]["ready"]
        self.commands.potato.usage = data["potato"]["usage"]

        self.commands.cdr.readyAt = getCmdCd(data["cdr"])
        self.commands.cdr.ready = data["cdr"]["ready"]

        self.commands.trample.readyAt = getCmdCd(data["trample"])
        self.commands.trample.ready = data["trample"]["ready"]
        self.commands.trample.usage = data["trample"]["trampleCount"]
        self.commands.trample.trampledCount = data["trample"]["trampledCount"]

        self.commands.steal.readyAt = getCmdCd(data["steal"])
        self.commands.steal.ready = data["steal"]["ready"]
        self.commands.steal.usage = data["steal"]["theftCount"]
        self.commands.steal.stolenCount = data["steal"]["stolenCount"]

        self.commands.quiz.readyAt = getCmdCd(data["quiz"])
        self.commands.quiz.ready = data["quiz"]["ready"]
        self.commands.quiz.attempted = data["quiz"]["attempted"]
        self.commands.quiz.completed = data["quiz"]["completed"]

        self.commands.eat.readyAt = getCmdCd(data["eat"])
        self.commands.eat.ready = data["eat"]["ready"]

        self.commands.gamble.wins = data["gamble"]["winCount"]
        self.commands.gamble.lost = data["gamble"]["loseCount"]
        self.commands.gamble.earned = data["gamble"]["totalWins"]
        self.commands.gamble.lost = data["gamble"]["totalLosses"]

        self.commands.duel.wins = data["duel"]["winCount"]
        self.commands.duel.losses = data["duel"]["loseCount"]
        self.commands.duel.earned = data["duel"]["totalWins"]
        self.commands.duel.lost = abs(data["duel"]["totalLosses"])
        self.commands.duel.caughtLosses = data["duel"]["caughtLosses"]

        stats.updatePlayer(self)
        if hadPlayer:
            stats.recordRefreshedBalanceChange(
                balanceCommand,
                balanceBeforeRefresh,
                responseText,
            )
        g.logger.info("Refreshed command cooldowns")



    def setShopCooldowns(self) -> None:
        ok, res = potat.execute("status")

        if not ok:
            raise Exception("Failed to get shop cooldowns: "
                            + res.get("text", res))

        message: str = res["text"].lower().strip()
        parts: list[str] = message.rsplit(" ● ", 4)[1:]
        cooldowns: dict[str, int] = {}

        for i in parts:
            item, cooldown = i.split(": ")
            cooldown = cooldown.strip()
            seconds = 0

            if "\u2705" not in cooldown:
                unit = "0s"
                for unit in cooldown.split(" and "):
                    seconds += int(unit[:-1]) * shortUnitToSeconds[unit[-1]]

                seconds += shortUnitToSeconds[unit[-1]] # status rounds down

            cooldowns[item] = int(time() + seconds)

        self.commands.shopQuiz.readyAt = cooldowns["shop-quiz"]
        self.commands.shopCdr.readyAt = cooldowns["shop-cdr"]
        self.commands.shopFertilizer.readyAt = cooldowns["shop-fertilizer"]
        self.commands.shopGuard.readyAt = cooldowns["shop-guard"]

        g.logger.info("Refreshed shop cooldowns")



    def setCooldowns(self, shop: bool = True) -> None:
        print()
        self.setData()
        if shop:
            self.setShopCooldowns()

        for command in self.commands.executable + self.commands.shopItems:
            if type(command) in [Rankup, Prestige]:
                continue
            if command.enabled:
                g.logger.debug(f"{command.name} ready {relative(command.readyAt - time())}")
        print()



    def executeCommands(self) -> None:
        executedCommand: bool = False

        for command in self.commands.executable:
            try:
                if command.canExecute:
                    executedCommand = True
                    self.executions += 1
                    g.logger.debug(f"{self.executions=}")
                    ok, res = command.execute(self.commands)
                    command.handleResult(ok, res)

                    if ok and isinstance(command, Cdr) and self.commands.shopCdr.canExecute:
                        shopok, shopres = self.commands.shopCdr._execute()
                        self.commands.shopCdr.handleResult(shopok, shopres)

                    if ok and isinstance(command, (Rankup, Prestige)):
                        responseText = str(
                            res.get("text", res.get("error", res.get("message", ""))),
                        )
                        self.setData(command.trigger, responseText)

                    if isinstance(command, Quiz):
                        quizResult = self.answerQuiz()
                        answer, balanceChange = quizResult if quizResult else (None, None)

                        stats.setLastCommand(command.trigger)
                        stats.recordCommandResult(f"a {answer}" if answer else command.trigger, "",
                            bool(not balanceChange), balanceChange)

                        shopok, shopres = self.commands.shopQuiz._execute()
                        self.commands.shopQuiz.handleResult(shopok, shopres)


                    elif isinstance(command, Prestige):
                        if not ok:
                            self.setData()
                        res = updatePrestigeStats(self)

                        if res.get("error"):
                            g.logger.error("Failed to update prestige stats: <Style.DIM>"
                                           + str(res["error"]),
                                           extra={"write": False})
                        else:
                            g.logger.info("Updated prestige stats", extra={"color": Fore.CYAN})

            except Exception as e:
                g.logger.error(f"Error while executing command \"{command.trigger}\"", exc_info=e,
                               extra={"webhook": True})

        if executedCommand:
            sleep(5)
            self.setCooldowns()



    def answerQuiz(self) -> tuple[str, tuple[int, int]] | None:
        sleep(5)

        balanceBefore = self.getPotatoCount()

        ok, res = potat.execute("quiz")

        quiz: str = res.get("text", "")

        firstExecution: bool = True
        if "forgot:" in quiz:
            quiz = quiz.split("forgot:", 1)[-1].strip()
            firstExecution = False

        elif not ok:
            errorMsg = ascii(str(res.get("text", res)))
            g.logger.error(f"Failed to get quiz: {errorMsg}",
                         extra={"data": res})
            return None


        quiz = quiz.removesuffix("(You have five minutes to answer correctly, time starts now!)")
        quiz = quiz.strip()

        answer = quizes.get(quiz)

        if not answer:
            g.logger.warning(f"Failed to answer quiz: No answer found for quiz: {quiz}")
            return None

        sleep(6)

        if self.commands.quiz.usePotat or firstExecution:
            ok, res = potat.execute(f"a {answer}")
        else:
            ok, res = twitch.send(self.channel.channelId, self.uid, str(answer))

        if not ok:
            errorMsg = ascii(str(res.get("text", res.get("error", res))))
            g.logger.error(f"Failed send quiz answer '{answer}': {errorMsg}",
                         extra={"data": res})
            return None

        balanceAfter = self.getPotatoCount()
        delta = balanceAfter - balanceBefore

        g.logger.info(f"Answered quiz (+{delta}): {answer}",
                      extra={"webhook": True})

        return (answer, (delta, balanceAfter))

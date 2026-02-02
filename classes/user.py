import json

from colorama import Fore, Style, Back
from time import time, sleep

from api import potat, twitch
from config import config
from config.inputs import canEnableTwitch
from classes.channel import PotatChannel
from classes.commands import Commands, Quiz, Rankup, Prestige
from classes.userdata import UserData
from prestige import updatePrestigeStats
from exceptions import StopBot
from logger import logger, cprint, clprint
from utils import shortUnitToSeconds, relative


with open("quizes.json", "r") as file:
    quizes: dict[str, str] = json.loads(file.read())



class User(UserData):
    def __init__(self) -> None:
        UserData.channel = PotatChannel(config.channelId, joinRequired=True)
        UserData.potatUser, UserData.potatUid = potat.getSelf()

        if not config.usePotat:
            if not canEnableTwitch():
                raise StopBot("Tried to use twitch api, but one or more twitch credentials are not set")
            
            UserData.twitchUser, UserData.twitchUid = twitch.getSelf()
            UserData.channel.setChannelData()

        else:
            UserData.twitchUser, UserData.twitchUid = ("", "")

        self.commands: Commands = Commands()
        self.executions: float = 0



    def setData(self) -> None:
        logger.debug("Setting user data")
        ok, data = potat.getUser(self.username)

        if not ok:
            if data.get("status") == 404:
                raise StopBot(f"Potat user '{self.username}' not found")
            
            logger.critical(f"Failed to get user stats: {data=}")
            raise Exception(f"Failed to get potat user data: {data.get("error", data)} ({data.get("status")})")
        
        d = data.get("potatoes")

        if not d:
            logger.critical(f"No potato data found for user '{self.username}'")
            raise StopBot(f"No potato data found for user '{self.username}'")
        
        self.joinedAt: str = d["joinedAt"]
        UserData.prestige = d["prestige"]
        UserData.rank = d["rank"]
        UserData.potatoes = d["count"]
        UserData.taxMultiplier = d["taxMultiplier"]
        self.verbose: bool = d["verbose"]

        self.commands.potato.readyAt = d["potato"]["readyAt"]
        self.commands.potato.ready = d["potato"]["ready"]
        self.commands.potato.usage = d["potato"]["usage"]

        self.commands.cdr.readyAt = int(d["cdr"]["readyAt"]) if d["cdr"]["readyAt"] else 0
        self.commands.cdr.ready = d["cdr"]["ready"]

        self.commands.trample.readyAt = d["trample"]["readyAt"]
        self.commands.trample.ready = d["trample"]["ready"]
        self.commands.trample.usage = d["trample"]["trampleCount"]
        self.commands.trample.trampledCount = d["trample"]["trampledCount"]
        
        self.commands.steal.readyAt = d["steal"]["readyAt"]
        self.commands.steal.ready = d["steal"]["ready"]
        self.commands.steal.usage = d["steal"]["theftCount"]
        self.commands.steal.stolenCount = d["steal"]["stolenCount"]
        
        self.commands.quiz.readyAt = d["quiz"]["readyAt"]
        self.commands.quiz.ready = d["quiz"]["ready"]
        self.commands.quiz.attempted = d["quiz"]["attempted"]
        self.commands.quiz.completed = d["quiz"]["completed"]

        self.commands.gamble.wins = d["gamble"]["winCount"]
        self.commands.gamble.lost = d["gamble"]["loseCount"]
        self.commands.gamble.earned = d["gamble"]["totalWins"]
        self.commands.gamble.lost = d["gamble"]["totalLosses"]

        self.commands.duel.wins = d["duel"]["winCount"]
        self.commands.duel.losses = d["duel"]["loseCount"]
        self.commands.duel.earned = d["duel"]["totalWins"]
        self.commands.duel.lost = abs(d["duel"]["totalLosses"])
        self.commands.duel.caughtLosses = d["duel"]["caughtLosses"]

        cprint("Refreshed command cooldowns")



    def setShopCooldowns(self) -> None:
        ok, res = potat.execute("status")

        if not ok:
            raise Exception(f"Failed to get shop cooldowns: {res.get("text", res.get("error", res))}")
                
        message: str = res["text"].lower().strip()
        parts: list[str] = message.rsplit(" ● ", 4)[1:]
        cooldowns: dict[str, int] = {}

        for i in parts:
            item, cooldown = i.split(": ")
            seconds = 0

            if cooldown != "\u2705":
                for unit in cooldown.split(" and "):
                    seconds += int(unit[:-1]) * shortUnitToSeconds[unit[-1]]
                
                seconds += shortUnitToSeconds[unit[-1]] # status rounds down
            
            cooldowns[item] = int(time() + seconds)

        self.commands.shopQuiz.readyAt = cooldowns["shop-quiz"]
        self.commands.shopCdr.readyAt = cooldowns["shop-cdr"]
        self.commands.shopFertilizer.readyAt = cooldowns["shop-fertilizer"]
        self.commands.shopGuard.readyAt = cooldowns["shop-guard"]

        cprint("Refreshed shop cooldowns")



    def setCooldowns(self, shop: bool = True) -> None:
        print()
        self.setData()
        if shop:
            self.setShopCooldowns()

        for command in self.commands.executable:
            if type(command) in [Rankup, Prestige]:
                continue
            if command.enabled:
                cprint(f"{command.trigger.replace(" ", "-")} ready {relative(command.readyAt - time())}", style=Style.DIM)
        print()
                


    def executeCommands(self) -> None:
        executedCommand: bool = False

        for command in self.commands.executable:
            try:
                if command.canExecute:
                    executedCommand = True
                    self.executions += 1
                    logger.debug(f"{self.executions=}")
                    ok, res = command.execute()


                    if not ok:
                        logger.error(f"Failed to execute command \"{command.trigger}\": {res=}")

                        message: str | dict = res.get("text", res.get("error", res.get("message", res)))
                        clprint(f"Failed to execute command \"{command.trigger}\":", ascii(str(message)), style=[Style.DIM], globalFore=Fore.RED)

                    else:
                        logger.debug(f"Executed command: {command.trigger}")

                        messages = [f"Executed command \"{command.trigger}\""]
                        if res.get("text"):
                            messages.append(ascii(res["text"]))

                        clprint(*messages, style=[Style.DIM])

                        if command.trigger.startswith("shop"):
                            sleep(6)

                    
                    if isinstance(command, Quiz):
                        self.answerQuiz()

                    elif isinstance(command, Prestige):
                        self.setData()
                        res = updatePrestigeStats(self)

                        if res.get("error"):
                            clprint("Failed to update prestige stats:", res["error"], style=[Style.DIM], globalFore=Fore.RED)
                        else:
                            cprint("Updated prestige stats", fore=Fore.CYAN)

            except Exception as e:
                logger.error(f"Error while executing command \"{command.trigger}\"", exc_info=e)
                clprint(f"Error while executing \"{command.trigger}\":", f"{type(e).__name__}: {str(e)}", style=[Style.DIM], globalFore=Fore.RED)

        if executedCommand:
            sleep(5)
            self.setCooldowns()



    def answerQuiz(self) -> None:
        sleep(6)

        ok, res = potat.execute("quiz")

        quiz: str = res.get("text", "")

        if "forgot:" in quiz:
            quiz = quiz.split("forgot:", 1)[-1].strip()
        
        elif not ok:
            logger.error(f"Failed to get quiz: {res}")
            error = ascii(str(res.get("text", res.get("error", res))))
            clprint("Failed to get quiz:", error, style=[Style.DIM], globalFore=Fore.RED)
            return
        
        
        quiz = quiz.removesuffix("(You have five minutes to answer correctly, time starts now!)")
        quiz = quiz.strip()

        answer = quizes.get(quiz)

        if not answer:
            logger.warning(f"No answer found for quiz: {quiz=}")
            clprint("Failed to answer quiz:", f"No answer found for quiz \"{quiz}\"", style=[Style.DIM], globalFore=Fore.RED)
            return
        
        sleep(6)

        if config.usePotat:
            ok, res = potat.execute(f"a {answer}")
        else:
            ok, res = twitch.send(self.channel.channelId, self.uid, str(answer))

        if not ok:
            logger.error(f"Failed send quiz answer: {res=}")
            error = ascii(str(res.get("text", res.get("error", res))))
            clprint(f"Failed to send quiz answer \"{answer}\":", error, style=[Style.DIM], globalFore=Fore.RED)
            return
        
        clprint("Answered quiz:", str(answer), style=[Style.DIM])
from time import sleep, time
from typing import TYPE_CHECKING

from colorama import Fore, Style

from api import potat, twitch
from api.exceptions import Unauthorized
from classes.userdata import UserData
from config import config
from logger import clprint, demojize, logger

if TYPE_CHECKING:
    from commands import Commands


class Command(UserData):
    trigger: str = ""
    baseCost: int = -1_000_000

    readyAt: float = 0
    ready: bool = False


    @property
    def name(self) -> str:
        return self.trigger.replace(" ", "-")


    @property
    def cost(self) -> int:
        return self.baseCost


    @property
    def enabled(self) -> bool:
        return config.farmingCommands[self.trigger]


    @property
    def canExecute(self) -> bool:
        if not self.enabled:
            return False
        if self.cost > self.potatoes:
            return False
        if self.ready:
            return True

        return self.readyAt < time()


    @property
    def usePotat(self) -> bool:
        return ((config.usePotat and self.name not in config.oppositePlatform)
                or (config.usePotat is False and self.name in config.oppositePlatform))



    def _execute(self) -> tuple[bool, dict]:
        logger.debug(f"Executing command: {self.trigger}")

        if self.usePotat:
            message = "@potatbotat " + self.trigger
            ok, res = potat.execute(message)

        else:
            message = self.channel.prefix + self.trigger
            try:
                ok, res = twitch.send(self.channel.channelId, self.uid, message)
            except Unauthorized:
                twitch.refreshAccessToken()
                ok, res = twitch.send(self.channel.channelId, self.uid, message)

        return ok, res


    def execute(self, commands: Commands) -> tuple[bool, dict]:
        return self._execute()


    def handleResult(self, ok: bool, res: dict) -> bool:
        if not ok:
            logger.error(f"Failed to execute command \"{self.trigger}\": {res=}")

            message: str | dict = res.get("text", res.get("error", res.get("message", res)))
            message = demojize(str(message), escape=True)
            clprint(f"Failed to execute command \"{self.trigger}\":", message,
                    style=[Style.DIM], globalFore=Fore.RED)
            return False

        logger.debug(f"Executed command: {self.trigger}")

        messages = [f"Executed command \"{self.trigger}\""]
        if res.get("text"):
            messages.append(demojize(res["text"], escape=True))

        clprint(*messages, style=[Style.DIM])

        if self.trigger.startswith("shop"):
            sleep(6)

        return True



class ShopItem(Command):
    @property
    def cost(self) -> int:
        return self.baseCost * self.rank


    @property
    def enabled(self) -> bool:
        return config.shopItems[self.name]

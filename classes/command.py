from __future__ import annotations

from time import sleep, time
from typing import TYPE_CHECKING

from colorama import Style

import globals as g
from api import potat, twitch
from api.exceptions import Unauthorized
from classes.userdata import UserData

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
        return g.config.farmingCommands[self.trigger]


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
        return ((g.config.usePotat and self.name not in g.config.oppositePlatform)
                or (g.config.usePotat is False and self.name in g.config.oppositePlatform))



    def _execute(self) -> tuple[bool, dict]:
        g.logger.debug(f"Executing command: {self.trigger}")

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
            g.logger.error(f"Failed to execute command \"{self.trigger}\": {res=}",
                           extra={"print": False})

            message: str | dict = res.get("text", res.get("error", res.get("message", res)))
            g.logger.error(f"Failed to execute command \"{self.trigger}\": {message}",
                           extra={"escape": True, "webhook": True})
            return False

        text = res.get("text", "")
        if text:
            text = f": <Style.NORMAL>{text}"

        g.logger.info(f"Executed command \"{self.trigger}\"{text}",
                      extra={"color": Style.DIM, "escape": True, "webhook": True,})

        if self.trigger.startswith("shop"):
            sleep(6)

        return True



class ShopItem(Command):
    @property
    def cost(self) -> int:
        return self.baseCost * self.rank


    @property
    def enabled(self) -> bool:
        return g.config.shopItems[self.name]

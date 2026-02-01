from time import time

from api import potat, twitch
from api.exceptions import Unauthorized
from classes.userdata import UserData
from config import config
from logger import logger


class Command(UserData):
    trigger: str = ""
    baseCost: int = -1_000_000

    readyAt: float = 0
    ready: bool = False
    

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
        if self.readyAt > time():
            return False
        return True



    def execute(self) -> tuple[bool, dict]:
        logger.debug(f"Executing command: {self.trigger}")

        if not config.usePotat:
            message = self.channel.prefix + self.trigger
            try:
                ok, res = twitch.send(self.channel.channelId, self.uid, message)
            except Unauthorized:
                twitch.refreshAccessToken()
                ok, res = twitch.send(self.channel.channelId, self.uid, message)
                
        else:
            message = "@potatbotat " + self.trigger
            ok, res = potat.execute(message)

        return ok, res



class ShopItem(Command):
    @property
    def cost(self) -> int:
        return self.baseCost * self.rank
    

    @property
    def enabled(self) -> bool:
        return config.shopItems[self.trigger.replace(" ", "-")]
from time import time

from api import potat, twitch
from exceptions import StopBot
from logger import logger


class PotatChannel:
    def __init__(self, channelId: str, joinRequired: bool = True) -> None:
        self.channelId: str = channelId
        self.joinRequired: bool = joinRequired

        self.lastDataCheck: float = 0
        self.lastUsernameCheck: float = 0
        
        self._prefix = ""
        self._username = ""


    def getChannelData(self) -> dict:
        ok, data = potat.getUser(self.username)

        if not ok:
            logger.critical(f"Failed to get potat channel data: {data=}")
            raise Exception(f"Failed to get potat channel data: {data.get("error", data)} ({data.get("status")})")
        
        channelData = data.get("channel")

        if not channelData or (self.joinRequired and channelData["state"] != "JOINED"):
            logger.critical(f"PotatBotat is not joined in '{self.username}': {data=}")
            raise StopBot(f"PotatBotat is not joined in '{self.username}'")
        
        self.internalId = data["user"]["user_id"]
        
        return channelData
    

    def setChannelData(self) -> None:
        data = self.getChannelData()

        self._prefix = data["settings"]["prefix"]

        self.lastDataCheck = time()



    @property
    def prefix(self) -> str:
        if self._prefix and self.lastDataCheck + 900 > time():
            return self._prefix
        
        self.setChannelData()
        return self._prefix
    
    @prefix.setter
    def prefix(self, value: str) -> None:
        self._prefix = value
    

    @property
    def username(self) -> str:
        if self._username and self.lastUsernameCheck + 3600*3 > time():
            return self._username
        
        channel = twitch.getUser(self.channelId).get("login")

        if not channel:
            raise StopBot(f"Channel with id '{self.channelId}' not found")
        
        self.lastUsernameCheck = time()

        self._username = channel
        return channel
    
    @username.setter
    def username(self, value: str) -> None:
        self._username = value
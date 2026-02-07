from classes.channel import PotatChannel
from config import config


class UserData:
    prestige: int = -1
    rank: int = -1
    potatoes: int = 0
    taxMultiplier: int = 1

    potatUser: str
    twitchUser: str
    twitchUid: str
    potatUid: str
    channel: PotatChannel


    @property
    def username(self) -> str:
        return self.potatUser if config.usePotat else self.twitchUser
    
    @property
    def uid(self) -> str:
        return self.potatUid if config.usePotat else self.twitchUid
import re
import json
from typing import Literal


filepath = "config.json"
defaultFarmingCommands = {
    "potato": True,
    "steal": True,
    "trample": False,
    "cdr": True,
    "quiz": False
}
defaultShopItems = {
    "shop-fertilizer": True,
    "shop-guard": True,
    "shop-cdr": True,
    "shop-quiz": False
}

type LoggingLevel = Literal[10, 20, 30, 40, 50]


class Config:
    def __init__(self) -> None:
        self.loadConfig()


    def loadConfig(self) -> None:
        try:
            with open(filepath, "r") as file:
                data: dict = json.load(file)

        except FileNotFoundError:
            raise Exception(f"No config.json file found")
        

        self.channelId: str = str(data.get("channelId", ""))
        self.twitchToken: str = str(data.get("twitchToken", ""))
        self.refreshToken: str = str(data.get("refreshToken", ""))
        self.clientId: str = str(data.get("clientId", ""))
        self.clientSecret: str = str(data.get("clientSecret", ""))
        self.authCode: str = str(data.get("authCode", ""))
        self.potatToken: str = str(data.get("potatToken", ""))
        self.printColor: bool = bool(data.get("printInColor"))
        self.printTime: bool = bool(data.get("printTime"))
        self.printEmojis: bool = bool(data.get("printEmojis"))
        self.usePotat: bool = bool(data.get("usePotatApi"))
        self.loggingLevel: LoggingLevel = data.get("loggingLevel", 30)


        if self.channelId and not re.fullmatch(r"\d*", self.channelId):
            raise ValueError("Config: channelId should be a string of numbers")

        if self.loggingLevel not in [10, 20, 30, 40, 50]:
            self.loggingLevel = 30


        self.farmingCommands: dict[str, bool] = {}
        farmingCommands = data.get("farmingCommands")
        if not farmingCommands or not isinstance(farmingCommands, dict):
            self.farmingCommands = defaultFarmingCommands
        
        else:
            for key, value in farmingCommands.items():
                if key not in defaultFarmingCommands:
                    continue

                if not isinstance(value, bool):
                    value = defaultFarmingCommands[key]

                self.farmingCommands[key] = value


        self.shopItems: dict[str, bool] = {}
        shopItems = data.get("shopItems")
        if not shopItems or not isinstance(shopItems, dict):
            self.shopItems = defaultShopItems
        
        else:
            for key, value in shopItems.items():
                if key not in defaultShopItems:
                    continue

                if not isinstance(value, bool):
                    value = defaultShopItems[key]

                self.shopItems[key] = value
        


    def dumpConfig(self) -> None:
        data = {
            "channelId": self.channelId,
            "twitchToken": self.twitchToken,
            "refreshToken": self.refreshToken,
            "clientId": self.clientId,
            "clientSecret": self.clientSecret,
            "authCode": self.authCode,
            "potatToken": self.potatToken,
            "printInColor": self.printColor,
            "printTime": self.printTime,
            "printEmojis": self.printEmojis,
            "usePotatApi": self.usePotat,
            "farmingCommands": self.farmingCommands,
            "shopItems": self.shopItems,
            "loggingLevel": self.loggingLevel
        }

        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)
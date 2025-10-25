import json

from colorama import Fore, Style, Back
from os import _exit

from logger import logger, cprint, clprint, setPrintColors


filePath = "config.json"



class Config:
    def __init__(self) -> None:
        logger.debug("Initializing config")

        try:
            with open(filePath, "r", encoding="utf-8") as file:
                data: dict = json.load(file)


        except FileNotFoundError:
            logger.warning("config.json file was not found")

            clprint("Please set up", "config.json", "or run", "setup.py", "before starting the bot", 
                    style=[None, Style.BRIGHT, None, Style.BRIGHT], globalFore=Fore.MAGENTA)
            input()
            _exit(1)

        except Exception as e:
            logger.error("Failed to get config", exc_info=e)

            clprint("Failed to read config file, check", "logs.log", "for detailed error data.", "Please make an issue on github or contact lolspers on twitch if this issue persists.", 
                    style=[None, Style.BRIGHT, None, Style.BRIGHT], globalFore=Fore.MAGENTA)
            input()
            _exit(1)


        try:
            self.color: bool = bool(data.get("printInColor"))

            setPrintColors(self.color)


            self.username: str = data["username"]
            self.userId: str = data["userId"]
            self.channelId: str = data["channelId"]

            self.userPrefix: str = data.get("userPrefix", "")
            self.channelPrefix: str = data.get("channelPrefix", "")
            self.potatToken: str | None = data.get("potatToken")

            self.twitchToken: str | None = data.get("twitchToken")
            self.clientId: str | None = data.get("clientId")
            self.refreshToken: str | None = data.get("refreshToken")
            self.clientSecret: str | None = data.get("clientSecret")

            self.usePotat: bool = data["usePotatApi"]

            self.enabledCommands: dict[str, bool] = data["farmingCommands"]
            self.enabledShopItems: dict[str, bool] = data["shopItems"]


            if isinstance(self.userId, int):
                self.userId = str(self.userId)

            if isinstance(self.channelId, int):
                self.channelId = str(self.channelId)


        except KeyError as e:
            clprint(f"Missing value in config.json:", str(e), "- please make sure", "'config.json'", "matches with", "'example-config.json'. " \
                    "If you used 'setup.py' or believe this is an error, please make an issue on github or contact lolspers on twitch.", 
                    style=[None, Style.BRIGHT, None, Style.BRIGHT, None, Style.BRIGHT], globalFore=Fore.MAGENTA)
            input()
            _exit(1)


        if self.usePotat and not self.potatToken:
            cprint("Using potat api, but no potat api token is set.", fore=Fore.MAGENTA)
            input()
            _exit(1)

        elif not self.usePotat and not self.twitchCredentialsSet():
            cprint("Using twitch api, but at least one of the twitch credentials is not set.", fore=Fore.MAGENTA)
            input()
            _exit(1)

        
        cprint("Loaded config", fore=Fore.CYAN)


    
    def updateConfig(self) -> None:
        data = {
            "username": self.username,
            "userId": self.userId,
            "channelId": self.channelId,
            "userPrefix": self.userPrefix,
            "channelPrefix": self.channelPrefix,
            "twitchToken": self.twitchToken,
            "clientId": self.clientId,
            "refreshToken": self.refreshToken,
            "clientSecret": self.clientSecret,
            "potatToken": self.potatToken,
            "usePotatApi": self.usePotat,
            "printInColor": self.color,
            "farmingCommands": self.enabledCommands,
            "shopItems": self.enabledShopItems
        }


        try:
            with open(filePath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

            logger.info("Updated config")


        except Exception as e:
            logger.error("Failed to update config file", exc_info=e)

            cprint("Failed to update config file. Please make an issue on github or contact lolspers on twitch if this issue persists.", fore=Fore.MAGENTA, style=Style.BRIGHT)



    def isEnabled(self, command: str) -> bool:
        if command.startswith("shop-"):
            return self.enabledShopItems[command]
        
        return self.enabledCommands[command]
    


    def toggleCommand(self, command: str) -> bool:
        enable = not self.isEnabled(command)

        if command.startswith("shop-"):
            self.enabledShopItems[command] = enable

        else:
            self.enabledCommands[command] = enable

        self.updateConfig()

        logger.info(f"Toggled '{command}', set to {enable}")
        
        return enable
    


    def enablePotat(self) -> bool:
        if self.potatToken is None:
            logger.warning("Tried to enable potat api but potatToken is not set")
            return False
        
        self.usePotat = True

        self.updateConfig()

        logger.info("Enabled sending messages through potat api")

        return True



    def enableTwitch(self) -> bool:
        if not self.twitchCredentialsSet():
            logger.warning("Tried to enable twitch api but a credential is not set")
            return False
        
        
        self.usePotat = False

        self.updateConfig()

        logger.info("Enabled sending messages through twitch api")

        return True
    


    def toggleColoredPrinting(self) -> bool:
        self.color = not self.color

        setPrintColors(self.color)

        self.updateConfig()

        logger.info("Toggled colored printing")

        return self.color




    def updateTwitchTokens(self, accessToken: str, refreshToken: str) -> None:
        self.twitchToken = accessToken
        self.refreshToken = refreshToken

        self.updateConfig()

        logger.info("Refreshed twitch token")



    def updateUserPrefix(self, prefix: str) -> None:
        self.userPrefix = prefix
        
        self.updateConfig()

        logger.debug(f"Updated user prefix, set to '{prefix}'")



    def updateChannelPrefix(self, prefix: str) -> None:
        self.channelPrefix = prefix
        
        self.updateConfig()

        logger.debug(f"Updated channel prefix, set to '{prefix}'")



    def twitchCredentialsSet(self) -> bool:
        if None in [self.twitchToken, self.clientId, self.refreshToken, self.clientSecret]:
            return False
        
        if "" in [self.twitchToken, self.clientId, self.refreshToken, self.clientSecret]:
            return False
        
        return True
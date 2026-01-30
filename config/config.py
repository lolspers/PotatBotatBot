import json
import re

from colorama import Fore, Style, Back

from logger import logger, cprint, clprint, setPrintColors, setPrintTime, killProgram
from api import potat, twitch


filePath = "config.json"



class Config:
    def __init__(self) -> None:
        logger.debug("Initializing config")

        try:
            with open(filePath, "r", encoding="utf-8") as file:
                data: dict = json.load(file)


        except FileNotFoundError:
            logger.warning("config.json file was not found")

            clprint("Please set up", "config.json", "before starting the bot", 
                    style=[None, Style.BRIGHT], globalFore=Fore.MAGENTA)
            
            killProgram()


        except Exception as e:
            logger.error("Failed to get config", exc_info=e)

            clprint("Failed to read config file, check", "logs.log", "for detailed error data.", "Please make an issue on github or contact lolspers on twitch if this issue persists.", 
                    style=[None, Style.BRIGHT, None, Style.BRIGHT], globalFore=Fore.MAGENTA)
            
            killProgram()


        try:
            self.color: bool = bool(data.get("printInColor"))
            self.time: bool = bool(data.get("printTime"))

            setPrintColors(self.color)
            setPrintTime(self.time)

            self.username: str
            self.channelId: str = data.get("channelId", "")

            self.channelPrefix: str = data.get("channelPrefix", "")
            self.potatToken: str = data.get("potatToken", "")

            twitch.accessToken = data.get("twitchToken", "")
            twitch.clientId = data.get("clientId", "")
            twitch.refreshToken = data.get("refreshToken", "")
            twitch.clientSecret = data.get("clientSecret", "")
            self.authCode: str | None = data.get("authCode")

            self.usePotat: bool = data["usePotatApi"]

            self.enabledCommands: dict[str, bool] = data["farmingCommands"]
            self.enabledShopItems: dict[str, bool] = data["shopItems"]

            self.loggingLevel: int = data.get("loggingLevel", 30)


        except KeyError as e:
            clprint(f"Missing value in config.json:", str(e), "- please make sure", "'config.json'", "matches with", "'example-config.json'. " \
                    "If you believe this is an error, please make an issue on github or contact lolspers on twitch.", 
                    style=[None, Style.BRIGHT, None, Style.BRIGHT, None, Style.BRIGHT], globalFore=Fore.MAGENTA)
            
            killProgram()


        logger.setLevel(self.loggingLevel)


        self.setupPotat()

        if not self.usePotat:
            successful = self.setupTwitch()

            if not successful:
                killProgram()
        

        if self.usePotat and not self.potatToken:
            cprint("Using potat api, but no potat api token is set.", fore=Fore.MAGENTA)
            
            killProgram()
        
        cprint("Loaded config\n", fore=Fore.CYAN)


    
    def setupPotat(self) -> bool:
        potat.setToken(self.potatToken)

        ok, res = potat.execute("user")

        if not ok:
            logger.critical(f"Config: failed to get self: {res=}")
            raise Exception(f"Failed to get self: {res.get("text", res)}")
        
            
        parts: list[str] = res["text"].split("●", 2)

        self.username = parts[0].strip().removeprefix("@").lower()

        return True



    def setupTwitch(self) -> bool:
        if self.authCode and not (twitch.accessToken and twitch.refreshToken):
            logger.info("Code set while access/refresh tokens are not, generating new tokens")
            cprint("Code found and twitch tokens are not set, generating twitch tokens...", style=Style.DIM)

            if not twitch.clientSecret:
                logger.warning("Tried to generate twitch tokens, but client secret is missing")
                cprint("Tried to generate twitch tokens, but client secret is missing", fore=Fore.MAGENTA)
                return False

            if not twitch.clientId:
                logger.warning("Tried to generate twitch tokens, but client id is missing")
                cprint("Tried to generate twitch tokens, but client id is missing", fore=Fore.MAGENTA)
                return False
            
            twitch.generateToken(code=self.authCode)

            self.authCode = ""
            twitch.refreshToken = twitch.refreshToken

            logger.info("Generated twitch tokens")
            cprint("Generated twitch tokens", fore=Fore.BLUE)

            self.updateConfig()


        elif not self.twitchCredentialsSet():
            logger.warning("Not all twitch credentials are set")
            cprint("Using twitch api, but at least one of the twitch credentials is not set.", fore=Fore.MAGENTA)
            return False
        

        if not self.channelId:
            logger.warning("Tried to setup twitch, but no channel id is set")
            cprint("Tried to use twitch api, but no channel id is set.", fore=Fore.MAGENTA)
            return False
        
        if not re.match(r"^\d+$", self.channelId):
            logger.warning("Tried to setup twitch, but channel id is not a number")
            cprint("Tried to use twitch api, but channel id is not a number.", fore=Fore.MAGENTA)
            return False


        twitch.setAuth()
        cprint("Validated twitch token", style=Style.DIM)

        self.updateConfig()

        return True



    def updateConfig(self) -> None:
        data = {
            "channelId": self.channelId,
            "channelPrefix": self.channelPrefix,
            "twitchToken": twitch.accessToken,
            "refreshToken": twitch.refreshToken,
            "clientId": twitch.clientId,
            "clientSecret": twitch.clientSecret,
            "authCode": self.authCode,
            "potatToken": self.potatToken,
            "printInColor": self.color,
            "printTime": self.time,
            "usePotatApi": self.usePotat,
            "farmingCommands": self.enabledCommands,
            "shopItems": self.enabledShopItems,
            "loggingLevel": self.loggingLevel
        }


        try:
            with open(filePath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

            logger.info("Updated config")


        except Exception as e:
            logger.error("Failed to update config file", exc_info=e)

            cprint("Failed to update config file. Please make an issue on github or contact lolspers on twitch if this issue persists.", fore=Fore.MAGENTA, style=Style.BRIGHT)



    def isEnabled(self, command: str) -> bool | None:
        try:
            if command.startswith("shop-"):
                return self.enabledShopItems[command]
            
            return self.enabledCommands[command]
        
        except KeyError as e:
            logger.warning("Config: Invalid command specified in isEnabled", exc_info=e)

            return None
    


    def toggleCommand(self, command: str) -> bool:
        enabled = self.isEnabled(command)
        enable = not enabled

        if enabled is None:
            return False
        

        if command.startswith("shop-"):
            self.enabledShopItems[command] = enable

        else:
            self.enabledCommands[command] = enable

        self.updateConfig()

        logger.info(f"Toggled '{command}', set to {enable}")
        
        return enable
    


    def enablePotat(self) -> bool:
        if not self.potatToken:
            logger.warning("Tried to enable potat api but potatToken is not set")
            return False
        
        self.setupPotat()

        self.usePotat = True

        self.updateConfig()

        logger.info("Enabled sending messages through potat api")

        return True



    def enableTwitch(self) -> bool:
        if not self.twitchCredentialsSet():
            logger.warning("Tried to enable twitch api but a credential is not set")
            cprint("Cannot enable twitch api: A required twitch credential in is not set in the config!", fore=Fore.MAGENTA)
            return False
        
        setUp = self.setupTwitch()

        if not setUp:
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
    


    def toggleTimePrinting(self) -> bool:
        self.time = not self.time

        setPrintTime(self.time)

        self.updateConfig()

        logger.info("Toggled time printing")

        return self.time



    def updateChannelPrefix(self, prefix: str) -> None:
        self.channelPrefix = prefix
        
        self.updateConfig()

        logger.debug(f"Updated channel prefix, set to '{prefix}'")



    def twitchCredentialsSet(self) -> bool:
        if None in [twitch.accessToken, twitch.clientId, twitch.refreshToken, twitch.clientSecret]:
            return False
        
        if "" in [twitch.accessToken, twitch.clientId, twitch.refreshToken, twitch.clientSecret]:
            return False
        
        return True
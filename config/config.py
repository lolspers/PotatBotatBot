import json
import re

from colorama import Fore, Style, Back

from logger import logger, cprint, clprint, setPrintColors, setPrintTime, killProgram
from .twitch import generateToken, validateToken
from api.potat import setAuth as setPotatAuth
from api.twitch import setAuth as setTwitchAuth


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


            self.username: str = data["username"]
            self.channelId: str = data.get("channelId", "")
            self.userId: str = ""

            self.userPrefix: str = data.get("userPrefix", "")
            self.channelPrefix: str = data.get("channelPrefix", "")
            self.potatToken: str = data.get("potatToken", "")

            self.twitchToken: str = data.get("twitchToken", "")
            self.clientId: str = data.get("clientId", "")
            self.refreshToken: str = data.get("refreshToken", "")
            self.clientSecret: str = data.get("clientSecret", "")
            self.authCode: str | None = data.get("authCode")

            self.usePotat: bool = data["usePotatApi"]

            self.enabledCommands: dict[str, bool] = data["farmingCommands"]
            self.enabledShopItems: dict[str, bool] = data["shopItems"]

            self.loggingLevel: int = data.get("loggingLevel", 30)

            
            setPotatAuth(token=self.potatToken)
            setTwitchAuth(token=self.twitchToken, clientId=self.clientId)


        except KeyError as e:
            clprint(f"Missing value in config.json:", str(e), "- please make sure", "'config.json'", "matches with", "'example-config.json'. " \
                    "If you believe this is an error, please make an issue on github or contact lolspers on twitch.", 
                    style=[None, Style.BRIGHT, None, Style.BRIGHT, None, Style.BRIGHT], globalFore=Fore.MAGENTA)
            
            killProgram()


        logger.setLevel(self.loggingLevel)


        if not self.usePotat:
            successful = self.setupTwitch()

            if not successful:
                killProgram()
        

        if self.usePotat and not self.potatToken:
            cprint("Using potat api, but no potat api token is set.", fore=Fore.MAGENTA)
            
            killProgram()
        
        cprint("Loaded config\n", fore=Fore.CYAN)


    
    def setupTwitch(self) -> bool:
        if self.authCode and not (self.twitchToken and self.refreshToken):
            logger.info("Code set while access/refresh tokens are not, generating new tokens")
            cprint("Code found and twitch tokens are not set, generating twitch tokens...", style=Style.DIM)

            if not self.clientSecret:
                logger.warning("Tried to generate twitch tokens, but client secret is missing")
                cprint("Tried to generate twitch tokens, but client secret is missing", fore=Fore.MAGENTA)
                return False


            if not self.clientId:
                logger.warning("Tried to generate twitch tokens, but client id is missing")
                cprint("Tried to generate twitch tokens, but client id is missing", fore=Fore.MAGENTA)
                return False
            
            authData: dict = generateToken(clientSecret=self.clientSecret, clientId=self.clientId, code=self.authCode)

            error: dict | None = authData.get("error")

            if error:
                message: str = error.get("message", "No error message provided")
                status: int = error.get("status")

                logger.warning(f"Failed to generate twitch tokens: {error}")
                clprint(f"Failed to generate twitch tokens ({status}):", message, style=[Style.BRIGHT], globalFore=Fore.MAGENTA)
                return False
            

            self.authCode = ""
            self.twitchToken = authData["access_token"]
            self.refreshToken = authData["refresh_token"]

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


        logger.info("Validating token...")

        tokenData: dict = validateToken(self.twitchToken)

        if tokenData.get("error"):
            if tokenData.get("status") == 401:
                logger.warning("Found token is invalid")
                cprint("Invalid access token found, please generate a new code.", fore=Fore.MAGENTA)
            else:
                logger.warning(f"Failed to validate token: {tokenData}")
                clprint(f"Failed to validate token:", tokenData["error"], style=[Style.BRIGHT], globalFore=Fore.MAGENTA)

            return False
        

        self.username = tokenData["login"]
        self.userId = tokenData["user_id"]

        logger.info("Validated twitch token")
        cprint("Validated twitch token", style=Style.DIM)

        self.updateConfig()

        return True



    def updateConfig(self) -> None:
        data = {
            "username": self.username,
            "channelId": self.channelId,
            "userPrefix": self.userPrefix,
            "channelPrefix": self.channelPrefix,
            "twitchToken": self.twitchToken,
            "refreshToken": self.refreshToken,
            "clientId": self.clientId,
            "clientSecret": self.clientSecret,
            "authCode": self.authCode,
            "potatToken": self.potatToken,
            "usePotatApi": self.usePotat,
            "printInColor": self.color,
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




    def updateTwitchTokens(self, accessToken: str, refreshToken: str) -> None:
        self.twitchToken = accessToken
        self.refreshToken = refreshToken

        self.updateConfig()
        
        setTwitchAuth(token=self.twitchToken, clientId=self.clientId)

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
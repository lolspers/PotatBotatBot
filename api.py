import requests

from colorama import Fore, Style
from time import time, sleep

from config import config
from logger import logger
from utils import shopItemPrice


twitchApi = "https://api.twitch.tv/helix/"
potatApi = "https://api.potat.app/"

lastChannelPrefixCheck = 0

unitToSeconds = {
    "s": 1, 
    "m": 60, 
    "h": 3600, 
    "d": 86400
}


class stopBot(Exception):
    pass

 

def twitchHeaders() -> dict:
    return {
        "Authorization": f"Bearer {config.twitchToken}",
        "Client-Id": config.clientId,
        "Content-Type": "application/json"
    }


def potatHeaders() -> dict:
    return {
        "Authorization": f"Bearer {config.potatToken}",
        "Content-Type": "application/json"
    }



def refreshToken():
    response = requests.post(
        url = "https://id.twitch.tv/oauth2/token", 
        params = {
            "client_id": config.clientId,
            "client_secret": config.clientSecret,
            "grant_type": "refresh_token",
            "refresh_token": config.refreshToken,
        }, 
        headers = {
            "Content-Type": "x-www-form-urlencoded"
        }
    )

    if response.status_code != 200:
        raise stopBot(f"Failed to refresh token: {response.json()}")
    
    
    data = response.json()

    config.updateTwitchTokens(accessToken=data["access_token"], refreshToken=data["refresh_token"])



def twitchSend(message: str, prefix: bool = True) -> tuple[bool, str]:
    if prefix:
        message = config.channelPrefix + message
    
    logger.debug(f"Sending message through twitch api: {message}")

    response = requests.post(
        url = twitchApi + "chat/messages", 
        headers = twitchHeaders(), 
        json = {
            "broadcaster_id": config.channelId,
            "sender_id": config.userId,
            "message": message
        }
    )

    data = response.json()

    if response.status_code != 200:
        if response.status_code == 401:
            if data["message"] == "Invalid OAuth token":
                refreshToken()

                return twitchSend(message, prefix=False)


        logger.error(f"Failed to send twitch message ({response.status_code}): {response.json()}")
        return (False, f"Failed to send twitch message ({response.status_code}): {data["message"]}")


    if data["data"][0]["is_sent"] is True:
        logger.debug(f"Sent twitch message: {message}")
        return (True, message)


    logger.warning(f"Twitch message dropped: {data}")

    return (False, f"Failed to send twitch message: {data["data"][0]["drop_reason"]["message"]}")



def getTwitchUser(uid: str) -> dict:
    response = requests.get(
        url = twitchApi + "users", 
        headers = twitchHeaders(), 
        params = {
            "id": str(uid)
        }
    )

    if response.status_code == 401:
        refreshToken()

        return getTwitchUser(uid)
    

    data = response.json()["data"]

    if not data:
        return {}
    
    return data[0]



def getPotatUser(username: str) -> dict:
    response = requests.get(potatApi + f"users/{username}")

    data = response.json()


    if response.status_code != 200 or data.get("statusCode") != 200:
        raise Exception(f"Failed to get potat user data ({response.status_code}/{data.get("statusCode")}): {data}")

    return data["data"][0]



def getPrefix(username: str) -> str | None:
    channelData = getPotatUser(username)

    if not channelData.get("channel"):
        return None

    prefix = channelData["channel"]["settings"]["prefix"]

    if isinstance(prefix, list):
        prefix = prefix[0]

    return prefix



def checkUserPrefix() -> None:
    logger.debug("Checking user prefix")

    prefix = getPrefix(config.username)

    if not prefix:
        raise stopBot("Failed to get prefix: PotatBotat is not joined in your channel")


    if config.userPrefix != prefix:
        config.updateUserPrefix(prefix)

        print(Style.DIM + Fore.CYAN + f"Updated user prefix to '{prefix}'")



def checkChannelPrefix() -> None:
    logger.debug("Checking channel prefix")

    channelData = getTwitchUser(config.channelId)

    if not channelData:
        raise stopBot("The provided channel id was not found!")
    
    
    channelName = channelData["login"]

    prefix = getPrefix(channelName)

    if not prefix:
        raise stopBot("Failed to get prefix: PotatBotat is not joined in the provided channel")


    if config.channelPrefix != prefix:
        config.updateChannelPrefix(prefix)

        print(Style.DIM + Fore.CYAN + f"Updated channel prefix to '{prefix}'")

        global lastChannelPrefixCheck
        lastChannelPrefixCheck = time()



def potatSend(message: str, cdRetries: int = 0) -> tuple[bool, str]:
    message = config.userPrefix + message

    logger.debug(f"Sending message through potat api: {message}")
    response = requests.post(potatApi+"execute", headers=potatHeaders(), json={"text": message})

    data = response.json()

    if response.status_code != 200:
        if response.status_code == 418:
            raise stopBot("Invalid PotatBotat token")
        
        elif response.status_code == 404:
            errors = data.get("errors")

            if errors and errors[0].get("message") == "Command invocation didn't return any result.":
                checkUserPrefix()


        logger.error(f"Failed to execute command '{message}' ({response.status_code}): {data}")
        return (False, f"{data} {response.status_code}")
    

    error = data["data"].get("error", ", ".join(data["errors"]))

    if error:
        if "⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: " in error:
            return (True, error.split("⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: ", 1)[1])
        
        if error == "󠀀⚠️ You did not answer your last quiz in time, and it expired... Run the command again to start a new quiz!":
            return potatSend("quiz")
        
        if "❌" not in error:
            logger.warning(f"Potat command error: {data}")

            if error.startswith("Command '") and error.endswith("' currently on cooldown.") and cdRetries > 0:
                sleep(1)

                logger.debug(f"Sent message again: {message=} - {error=}")

                return potatSend(message, cdRetries-1)
            
            return (False, f"Failed to execute command: {error}")
        
        result = error
    

    elif data["data"] == {}:
        return (True, "Command returned no result")

    else:
        result = data["data"]["text"]

    if result.startswith("✋⏰") or "ryanpo1Bwuh ⏰" in result:
        logger.warning("Tried to execute command while on cooldown: {data}")

        return (False, f"PotatBotat command '{message}' still on cooldown: {result}")
    
    if " (You have five minutes to answer correctly, time starts now!)" in result:
        return (True, result.replace(" (You have five minutes to answer correctly, time starts now!)", ""))

    return (True, f"{message} - {result}")



def getPotatoData() -> dict:
    data = getPotatUser(config.username)

    potatoData = data["potatoes"]

    potatoes = potatoData["count"]
    rank = potatoData["rank"]
    prestige = potatoData["prestige"]

    cooldowns = {
        "potato": potatoData["potato"]["readyAt"],
        "steal": potatoData["steal"]["readyAt"],
        "trample": potatoData["trample"]["readyAt"],
        "cdr": potatoData["cdr"]["readyAt"],
        "quiz": potatoData["quiz"]["readyAt"]
    }
    filteredCooldowns = {}

    for command, cooldown in cooldowns.items():
        if not config.isEnabled(command):
            continue

        if cooldown is None:
            filteredCooldowns[command] = 0

        else:
            filteredCooldowns[command] = int(cooldown/1000 + 1)
    
    
    logger.debug(f"Updated cooldowns: {filteredCooldowns}")

    return {"potatoes": potatoes, "rank": rank, "prestige": prestige, "cooldowns": filteredCooldowns}



def getShopCooldowns() -> dict[str, float]:
    ok, result = potatSend("status")

    if not ok:
        raise Exception(f"Failed to get shop cooldowns: {result}")
    

    rawCooldowns = result.split(": ", 2)[2].replace("\u2705", "0s").lower()

    potatCooldowns = {
        cooldown.split(": ", 1)[0]: cooldown.split(": ", 1)[1]
        for cooldown in rawCooldowns.split(" ● ")
        if cooldown.startswith("shop-")
    }
    

    shopCooldowns = {}

    for command in potatCooldowns:
        if not config.isEnabled(command):
            continue

        cooldowns = potatCooldowns[command].split(" and ")
        readyIn = time()

        for cooldown in cooldowns:
            if not "s" in cooldown:
                readyIn += 60 # status rounds down

            readyIn += int(cooldown[:-1]) * unitToSeconds[cooldown[-1]]

        shopCooldowns.update({command: readyIn})


    logger.debug(f"New shop cooldowns: {shopCooldowns}")

    return shopCooldowns



def buyItem(item: str, rank: int, potatoes: int) -> bool:
    price = shopItemPrice(item=item, rank=rank)

    if potatoes < price:
        return False
    

    ok, data = send(f"shop {item}")

    if ok:
        print(f"Bought shop item: {data}")

    else:
        print(Fore.RED + f"Failed to buy shop item: {data}")

    return True



def send(message: str) -> tuple[bool, str]:
    if config.usePotat:
        return potatSend(message)

    else:
        if time() > lastChannelPrefixCheck + 3600:
            checkChannelPrefix()

        return twitchSend(message)



if not config.userPrefix:
    checkUserPrefix()
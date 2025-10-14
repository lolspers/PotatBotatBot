import requests
from time import time, sleep

from config import *
from data import log, getConfig, updateConfig
from priceUtils import shopItemPrice


config = getConfig()

twitchToken = config["twitchToken"]
clientId = config["clientId"]
channelId = config["channelId"]
userPrefix = config.get("userPrefix")
channelPrefix = config.get("channelPrefix")
userId = config["userId"]
potatToken = config["potatToken"]
username = config["username"]
usePotatApi = config["usePotatApi"]
farmingCommands = config["farmingCommands"]
shopItems = config["shopItems"]

lastChannelPrefixCheck = 0


class stopBot(Exception):
    pass


twitchHeaders = {
    "Authorization": f"Bearer {twitchToken}",
    "Client-Id": clientId,
    "Content-Type": "application/json"
}
twitchBody = {
    "broadcaster_id": channelId,
    "sender_id": userId,
    "message": None
}

potatHeaders = {
    "Authorization": f"Bearer {potatToken}",
    "Content-Type": "application/json"
}



def refreshToken():
    response = requests.post("https://id.twitch.tv/oauth2/token", params = {
        "client_id": clientId,
        "client_secret": config["clientSecret"],
        "grant_type": "refresh_token",
        "refresh_token": config["refreshToken"],
    }, headers = {
        "Content-Type": "x-www-form-urlencoded"
    })
    if response.status_code != 200:
        raise stopBot(f"Failed to refresh token: {response.json()}")
    
    data = response.json()
    global twitchToken
    twitchToken = data["access_token"]
    config["twitchToken"] = twitchToken
    twitchHeaders["Authorization"] = f"Bearer {twitchToken}"
    config["refreshToken"] = data["refresh_token"]

    updateConfig(config)



def twitchSend(message: str, prefix: bool = True) -> str:
    if prefix:
        message = channelPrefix + message

    twitchBody["message"] = message
    

    response = requests.post(twitchApi+"chat/messages", headers=twitchHeaders, json=twitchBody)

    data = response.json()

    if response.status_code != 200:
        if response.status_code == 401:
            if data["message"] == "Invalid OAuth token":
                refreshToken()
                return twitchSend(message, prefix=False)

        log(f"TWITCH ERROR : {response.json()} {response.status_code}")
        return f"Failed to send twitch message ({response.status_code}): {data["message"]}"

    if data["data"][0]["is_sent"] is True:
        return f"Successfully sent twitch message: '{message}'"

    dropReason = data["data"][0]["drop_reason"]["message"]
    log(f"TWITCH DROP ERROR : {response.json()}")
    return f"Failed to sent twitch message: {dropReason}"



def getTwitchUser(uid: str) -> dict:
    response = requests.get(twitchApi+"users", headers=twitchHeaders, params={"id": str(uid)})

    if response.status_code == 401:
        raise stopBot("Invalid twitch token")
    

    data = response.json()["data"]

    if not data:
        return {}
    
    return data[0]



def getPotatUser(username: str) -> dict:
    response = requests.get(potatApi + f"users/{username}")

    if response.status_code != 200:
        log(f"Failed to get twitch user data: {response.json()} {response.status_code}")
        raise Exception(f"Failed to get potat user data: {response.json()} {response.status_code}")

    data = response.json()

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
    prefix = getPrefix(username)

    if not prefix:
        raise stopBot("Failed to get prefix: PotatBotat is not joined in your channel")


    if userPrefix != prefix:
        global userPrefix
        userPrefix = prefix

        config.update({"userPrefix": prefix})
        updateConfig(config)

        print(f"Updated user prefix to '{prefix}'")


def checkChannelPrefix() -> None:
    channelData = getTwitchUser(channelId)

    if not channelData:
        raise stopBot("The provided channel id was not found!")
    
    channelName = channelData["login"]

    prefix = getPrefix(channelName)

    if not prefix:
        raise stopBot("Failed to get prefix: PotatBotat is not joined in the provided channel")


    if channelPrefix != prefix:
        global channelPrefix
        channelPrefix = prefix

        config.update({"channelPrefix": prefix})
        updateConfig(config)

        print(f"Updated channel prefix to '{prefix}'")

        global lastChannelPrefixCheck
        lastChannelPrefixCheck = time()



def potatSend(message: str, cdRetries: int = 0) -> str:
    response = requests.post(potatApi+"execute", headers=potatHeaders, json={"text": userPrefix + message})

    if response.status_code != 200:
        if response.status_code == 418:
            log(f"INVALID POTAT TOKEN: {response.json()}")
            print("Invalid potatbotat token")
            raise stopBot("Invalid PotatBotat token")
        
        elif response.status_code == 404:
            try:
                data = response.json()

                if data.get("errors", [{}])[0].get("message") == "Command invocation didn't return any result.":
                    
                    checkChannelPrefix()


            except Exception:
                pass


        log(f"POTAT ERROR : {response.json()} {response.status_code}")
        return f"{response.json()} {response.status_code}"
    
    data = response.json()

    error = data["data"].get("error", ", ".join(data["errors"]))
    if error:
        if "⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: " in error:
            return error.split("⚠️ You already have an existing quiz in progress! Here is the question in case you forgot: ", 1)[1]
        
        if error == "󠀀⚠️ You did not answer your last quiz in time, and it expired... Run the command again to start a new quiz!":
            return potatSend("quiz")
        
        if "❌" not in error:
            log(f"POTAT ERROR : {response.json()}")
            if error.startswith("Command '") and error.endswith("' currently on cooldown.") and cdRetries > 0:
                sleep(1)
                log(f"Sent message again: {message=} - {error=}")
                return potatSend(message, cdRetries-1)
            return f"Failed to execute command: {error}"
        result = error
    
    elif data["data"] == {}:
        return "Command returned no result"

    else:
        result = data["data"]["text"]

    if result.startswith("✋⏰") or "ryanpo1Bwuh ⏰" in result:
        log(f"COOLDOWN : {response.json()}")
        return f"PotatBotat command '{message}' not ready yet: {result}"
    
    if " (You have five minutes to answer correctly, time starts now!)" in result:
        return result.replace(" (You have five minutes to answer correctly, time starts now!)", "")

    return f"Executed command: '{message}': {result}"


def getPotatoData() -> dict:
    data = getPotatUser(username)

    potatoData = data[0]["potatoes"]

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

    for cooldown in cooldowns:
        if farmingCommands[cooldown] is False:
            continue
        if cooldowns[cooldown] is None:
            filteredCooldowns[cooldown] = 0
        else:
            filteredCooldowns[cooldown] = cooldowns[cooldown]/1000
    
    print(filteredCooldowns)

    return {"potatoes": potatoes, "rank": rank, "prestige": prestige, "cooldowns": filteredCooldowns}



def getShopCooldowns() -> dict:
    potatStatus = potatSend("status")
    if not potatStatus.startswith("Executed command"):
        raise Exception(f"Failed to get shop cooldowns: {potatStatus}")
    
    # Example message: Potato: 28m and 23s ● Cooldown: ✅ ● Trample: ✅ ● Steal: 1h and 48m ● Eat: 26m and 12s ● Quiz: 41m and 54s ● Shop-Quiz: ✅ ● Shop-Cdr: 15h and 53m ● Shop-Fertilizer: ✅ ● Shop-Guard: ✅

    potatStatus = potatStatus.split(": ", 2)[2].replace("✅", "0s").lower()
    potatCooldowns = {}
    unitToSeconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}

    [potatCooldowns.update({cooldown.split(": ", 1)[0]: cooldown.split(": ", 1)[1]}) for cooldown in potatStatus.split(" ● ")]

    shopCooldowns = {}
    for command in potatCooldowns:
        if not shopItems.get(command, False):
            continue

        cooldowns = potatCooldowns[command].split(" and ")
        readyIn = time()

        for cooldown in cooldowns:
            if not "s" in cooldown:
                readyIn += 60 # status rounds minutes down
            readyIn += int(cooldown[:-1]) * unitToSeconds[cooldown[-1]]

        shopCooldowns[command] = readyIn

    print(shopCooldowns)
    return shopCooldowns


def buyItem(item: str, rank: int, potatoes: int) -> bool:
    price = shopItemPrice(item=item, rank=rank)

    if potatoes < price:
        return False
    

    res = send(f"shop {item}")
    print(res)

    return True



def send(message: str):
    if usePotatApi:
        return potatSend(message)
    else:
        if time() > lastChannelPrefixCheck + 3600:
            checkChannelPrefix()

        return twitchSend(message)



if not userPrefix:
    checkUserPrefix()
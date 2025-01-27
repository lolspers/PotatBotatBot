from config import *
import requests
from data import log, getConfig, updateConfig

config = getConfig()

twitchToken = config["twitchToken"]
clientId = config["clientId"]
channelId = config["channelId"]
userId = config["userId"]
potatToken = config["potatToken"]
username = config["username"]
usePotatApi = config["usePotatApi"]
farmingCommands = config["farmingCommands"]

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
    config["twitchToken"] = data["access_token"]
    global twitchToken
    twitchToken = data["access_token"]
    config["refreshToken"] = data["refresh_token"]

    updateConfig(config)

def twitchSend(message: str) -> str:
    twitchBody["message"] = message
    
    response = requests.post(twitchApi+"chat/messages", headers=twitchHeaders, json=twitchBody)
    data = response.json()
    if response.status_code != 200:
        if response.status_code == 401:
            refreshToken()
            log(f"INVALID TWITCH TOKEN: {response.json()}")
            print("Invalid twitch token")

        log(f"TWITCH ERROR : {response.json()} {response.status_code}")
        return f"Failed to send twitch message ({response.status_code}): {data["message"]}"

    if data["data"][0]["is_sent"] is True:
        return f"Successfully sent twitch message: '{message}'"

    dropReason = data["data"][0]["drop_reason"]["message"]
    log(f"TWITCH DROP ERROR : {response.json()}")
    return f"Failed to sent twitch message: {dropReason}"


def potatSend(message: str) -> str:
    response = requests.post(potatApi+"execute", headers=potatHeaders, json={"text": message})
    if response.status_code != 200:
        if response.status_code == 418:
            log(f"INVALID POTAT TOKEN: {response.json()}")
            print("Invalid potatbotat token")
            raise stopBot

        log(f"POTAT ERROR : {response.json()} {response.status_code}")
        return f"{response.json()} {response.status_code}"
    
    data = response.json()

    error = data["data"].get("error", ", ".join(data["errors"]))
    if error:
        if "❌" not in error:
            log(f"ERROR : {response.json()}")
            return f"Failed to execute command: {error}"
        result = error
    
    elif data["data"] == {}:
        return "Command returned no result"

    else:
        result = data["data"]["text"]

    if result.startswith("✋⏰") or "ryanpo1Bwuh ⏰" in result:
        log(f"COOLDOWN : {response.json()}")
        return f"PotatBotat command '{message}' not ready yet: {result}"

    return f"Executed command: '{message}': {result}"


def getPotatoData() -> dict:
    response = requests.get(potatApi+"users/"+username)
    if response.status_code != 200:
        log(f"POTAT DATA ERROR : {response.json()} {response.status_code}")
        return f"{response.json()} {response.status_code}"

    data = response.json()
    potatoData = data["data"][0]["potatoes"]

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

def send(message: str):
    message = potatPrefix+message
    if usePotatApi:
        return potatSend(message)
    else:
        return twitchSend(message)

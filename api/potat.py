import requests

from time import sleep

from logger import logger
from exceptions import StopBot
from .exceptions import PotatNoResult


url = "https://api.potat.app/"

lastChannelPrefixCheck = 0

headers: dict[str, str] = {
    "Content-Type": "application/json"
}



def setAuth(token: str) -> None:
    global headers

    headers.update({
        "Authorization": f"Bearer {token}"
    })



def getSelf() -> dict[str, str]:
    ok, message = potatSend("u")
    
    if not ok:
        logger.critical(f"Failed to get self: {message}")
        raise StopBot(f"Failed to get self: {message}")
    

    parts = message.split(" - ", 1)[1].split(" ● ", 2)

    username = parts[0].removeprefix("@").lower()
    uid = parts[1].split("ID: ", 1)[1]
    
    return {
        "login": username,
        "uid": uid
    }



def getPotatUser(username: str) -> dict:
    response = requests.get(url + f"users/{username}")

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



def getChannelPrefix(channel: str) -> str:
    logger.debug("Checking channel prefix")

    prefix = getPrefix(channel)

    if not prefix:
        raise StopBot("Failed to get prefix: PotatBotat is not joined in the provided channel")

    return prefix



def potatSend(message: str, cdRetries: int = 0) -> tuple[bool, str]:
    if not message.lower().startswith("@potatbotat"):
        message = f"@potatbotat {message}"
    
    logger.debug(f"Sending message through potat api: {message}")
    response = requests.post(url+"execute", headers=headers, json={"text": message})

    data = response.json()

    if response.status_code != 200:
        logger.error(f"Failed to execute command '{message}' ({response.status_code}): {data}")

        if response.status_code == 418:
            raise StopBot("Invalid PotatBotat token")
        
        elif response.status_code == 404:
            errors = data.get("errors")

            if errors and errors[0].get("message") == "Command invocation didn't return any result.":
                raise PotatNoResult()

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
        result: str = data["data"]["text"]

    if result.startswith("✋⏰") or "ryanpo1Bwuh ⏰" in result:
        logger.warning("Tried to execute command while on cooldown: {data}")

        return (False, f"PotatBotat command '{message}' still on cooldown: {result}")
    
    if " (You have five minutes to answer correctly, time starts now!)" in result:
        return (True, result.replace(" (You have five minutes to answer correctly, time starts now!)", ""))
    
    
    result = result.strip().removeprefix("●").strip()

    return (True, f"{message} - {result}")
import requests

from logger import logger
from exceptions import StopBot
from .exceptions import Unauthorized


url = "https://api.twitch.tv/helix/"


headers: dict[str, str] = {
    "Content-Type": "application/json"
}



def setAuth(token: str, clientId: str) -> None:
    global headers

    headers.update({
        "Authorization": f"Bearer {token}",
        "Client-Id": clientId
    })



def refreshToken(clientSecret: str, clientId: str, refreshToken: str) -> dict:
    response = requests.post(
        url = "https://id.twitch.tv/oauth2/token", 
        params = {
            "client_id": clientId,
            "client_secret": clientSecret,
            "grant_type": "refresh_token",
            "refresh_token": refreshToken,
        }, 
        headers = {
            "Content-Type": "x-www-form-urlencoded"
        }
    )

    if response.status_code != 200:
        raise StopBot(f"Failed to refresh token: {response.json()}")
    
    
    data = response.json()

    return {
        "accessToken": data["access_token"],
        "refreshToken": data["refresh_token"]
    }



def twitchSend(channelId: str, userId: str, message: str) -> tuple[bool, str]:
    logger.debug(f"Sending message through twitch api: {message}")

    response = requests.post(
        url = url + "chat/messages", 
        headers = headers, 
        json = {
            "broadcaster_id": channelId,
            "sender_id": userId,
            "message": message
        }
    )

    data = response.json()

    if response.status_code != 200:
        if response.status_code == 401:
            if data["message"] == "Invalid OAuth token":
                raise Unauthorized()


        logger.error(f"Failed to send twitch message ({response.status_code}): {response.json()}")
        return (False, f"Failed to send twitch message ({response.status_code}): {data["message"]}")


    if data["data"][0]["is_sent"] is True:
        logger.debug(f"Sent twitch message: {message}")
        return (True, message)


    logger.warning(f"Twitch message dropped: {data}")

    return (False, f"Failed to send twitch message: {data["data"][0]["drop_reason"]["message"]}")



def getTwitchUser(uid: str) -> dict:
    response = requests.get(
        url = url + "users", 
        headers = headers, 
        params = {
            "id": str(uid)
        }
    )

    if response.status_code == 401:
        raise Unauthorized()
    

    data = response.json()["data"]

    if not data:
        return {}
    
    return data[0]
from time import sleep

import requests

import globals as g
from exceptions import StopBot

from .apiClient import ApiClient

oauthUrl = "https://id.twitch.tv/oauth2"


class TwitchApi(ApiClient):
    def __init__(self) -> None:
        self.name: str = "TwitchApi"
        self.url: str = "https://api.twitch.tv/helix"
        self.headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": g.config.twitchToken,
            "Client-Id": g.config.clientId,
        }


    def getUser(self, uid: str) -> dict:
        params: dict = {
            "id": uid,
        }
        ok, res = self._request("GET", "/users", params=params)

        return res["data"][0] if ok and res["data"] else {}


    def send(self, channelId: str, userId: str, message: str) -> tuple[bool, dict]:
        json= {
            "broadcaster_id": channelId,
            "sender_id": userId,
            "message": message,
        }

        g.logger.debug(f"Sending message through twitch api: {json=}",
                       extra={"print": False})
        ok, res = self._request("POST", "/chat/messages", json=json)

        if not ok:
            g.logger.error("Failed to send twitch message " \
                           f"({res.get("status", "Unknown status")}): {res!s}",
                           extra={"print": False})
            return False, res

        if res["data"][0]["is_sent"] is True:
            g.logger.debug(f"Sent twitch message: {res=}",
                         extra={"print": False})
            sleep(1) # twitch no badge ratelimit
            return True, res

        g.logger.warning(f"Twitch message dropped: {res=}",
                       extra={"print": False})
        return False, res


    def generateToken(self) -> None:
        data: dict = {
            "client_secret": g.config.clientSecret,
            "client_id": g.config.clientId,
            "code": g.config.authCode,
            "redirect_uri": "http://localhost",
            "grant_type": "authorization_code",
        }
        response = requests.post(oauthUrl+"/token", data=data)
        data = response.json()

        if not response.ok:
            g.logger.critical(f"Failed to generate twitch token: {data=}",
                              extra={"print": False})
            raise StopBot(f"Failed to generate twitch token: {data.get("message", data)}, " \
                          "please try generating a new code")

        g.config.twitchToken = data["access_token"]
        g.config.refreshToken = data["refresh_token"]
        g.config.dumpConfig()


    def refreshAccessToken(self) -> None:
        g.logger.debug("Refreshing access token")
        params: dict = {
            "client_id": g.config.clientId,
            "client_secret": g.config.clientSecret,
            "grant_type": "refresh_token",
            "refresh_token": g.config.refreshToken,
        }
        headers: dict = {
            "Content-Type": "x-www-form-urlencoded",
        }
        response = requests.post(url=oauthUrl+"/token", params=params, headers=headers)

        if response.status_code != 200:
            raise StopBot(f"Failed to refresh token: {response.json()}")

        data = response.json()

        g.config.twitchToken = data["access_token"]
        g.config.refreshToken = data["refresh_token"]
        g.config.authCode = ""

        self.headers["Authorization"] = f"Bearer {g.config.twitchToken}"
        g.config.dumpConfig()


    def validateToken(self) -> tuple[bool, dict]:
        g.logger.debug("Validating twitch token")

        headers: dict = {
            "Authorization": f"Bearer {g.config.twitchToken}",
        }

        response = requests.get(oauthUrl+"/validate", headers=headers)
        data: dict = response.json()
        g.logger.debug(f"TwitchApi: validateToken: {data=} ({response.status_code})")

        result: dict = {
            "status": response.status_code,
            "message": "No message provided",
        }

        if response.status_code == 401:
            result["message"] = "Invalid access token"
            return False, result

        result.update({
            "clientId": data["client_id"],
            "login": data["login"],
            "userId": data["user_id"],
            "scopes": data["scopes"],
        })

        return True, result


    def getSelf(self) -> tuple[str, str]:
        ok, res = self.validateToken()

        if not ok:
            self.refreshAccessToken()
            ok, res = self.validateToken()

            if not ok:
                raise StopBot("Failed to validate token after refreshing the token")

        scopes: list[str] = res["scopes"]
        if "user:write:chat" not in scopes:
            raise StopBot("Token is missing the \"user:write:chat\" scope")

        self.headers.update({
            "Client-id": g.config.clientId,
            "Authorization": f"Bearer {g.config.twitchToken}",
        })

        userId = res["userId"]
        username = res["login"]

        return username, userId

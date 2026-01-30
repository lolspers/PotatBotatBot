import requests

from .apiClient import ApiClient
from exceptions import StopBot
from logger import logger


oauthUrl = "https://id.twitch.tv/oauth2"


class TwitchApi(ApiClient):
    def __init__(self) -> None:
        self.name: str = "TwitchApi"
        self.url: str = "https://api.twitch.tv/helix"
        self.headers: dict[str, str] = {
            "Content-Type": "application/json"
        }

        self.clientSecret: str
        self.clientId: str
        self.accessToken: str
        self.refreshToken: str
        self.userId: str


    def getUser(self, uid: str) -> dict:
        params: dict = {
            "id": uid
        }
        ok, res = self._request("GET", "/users", params=params)

        return res["data"][0] if ok and res["data"] else {}


    def send(self, channelId: str, message: str) -> tuple[bool, dict]:
        json= {
            "broadcaster_id": channelId,
            "sender_id": self.userId,
            "message": message
        }

        logger.debug(f"Sending message through twitch api: {json=}")
        ok, res = self._request("POST", "/chat/messages", json=json)

        if not ok:
            logger.error(f"Failed to send twitch message ({res.get("status", "Unknown status")}): {res}")
            return False, res

        if res["data"][0]["is_sent"] is True:
            logger.debug(f"Sent twitch message: {res=}")
            return True, res

        logger.warning(f"Twitch message dropped: {res=}")
        return False, res


    def generateToken(self, code: str) -> None:
        data: dict = {
            "client_secret": self.clientSecret,
            "client_id": self.clientId,
            "code": code,
            "redirect_uri": "http://localhost",
            "grant_type": "authorization_code"
        }
        response = requests.post(oauthUrl+"/token", data=data)
        data = response.json()

        if not response.ok:
            logger.critical(f"Failed to generate twitch token: {data=}")
            raise StopBot(f"Failed to generate twitch token: {data.get("message", data)}, please try generating a new code")
        
        self.accessToken = data["access_token"]
        self.refreshToken = data["refresh_token"]
        self.setAuth()
    

    def refreshAccessToken(self) -> None:
        logger.info("Refreshing access token")
        params: dict = {
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
            "grant_type": "refresh_token",
            "refresh_token": self.refreshToken,
        }
        headers: dict = {
            "Content-Type": "x-www-form-urlencoded"
        }
        response = requests.post(url=oauthUrl+"/token", params=params, headers=headers)

        if response.status_code != 200:
            raise StopBot(f"Failed to refresh token: {response.json()}")
        
        data = response.json()

        self.accessToken = data["access_token"]
        self.refreshToken = data["refresh_token"]

        self.headers["Authorization"] = f"Bearer {self.accessToken}"
    

    def validateToken(self) -> tuple[bool, dict]:
        logger.debug(f"Validating twitch token")

        headers: dict = {
            "Authorization": f"Bearer {self.accessToken}"
        }

        response = requests.get(oauthUrl+"/validate", headers=headers)
        data: dict = response.json()
        logger.debug(f"TwitchApi: validateToken: {data=} ({response.status_code})")

        result: dict = {
            "status": response.status_code,
            "message": "No message provided"
        }

        if response.status_code == 401:
            result["message"] = "Invalid access token"
            return False, result

        result.update({
            "clientId": data["client_id"],
            "login": data["login"],
            "userId": data["user_id"],
            "scopes": data["scopes"]
        })

        return True, result
    

    def setAuth(self) -> None:
        ok, res = self.validateToken()

        if not ok:
            self.refreshAccessToken()
            ok, res = self.validateToken()

            if not ok:
                raise StopBot(f"Failed to validate token after refreshing the token")

        scopes: list[str] = res["scopes"]
        if "user:write:chat" not in scopes:
            raise StopBot("Token is missing the \"user:write:chat\" scope")

        self.userId = res["userId"]

        self.headers.update({
            "Client-id": self.clientId,
            "Authorization": f"Bearer {self.accessToken}"
        })
import requests

from .exceptions import Unauthorized
from logger import logger



class PotatApi:
    def __init__(self) -> None:
        self.url: str = "https://api.potat.app"
        self.headers: dict[str, str] = {
            "Content-Type": "application/json"
        }

    
    def _request(self, method: str, endpoint: str, params: dict | None = None, json: dict | None = None) -> tuple[bool, dict]:
        url = self.url + endpoint
        logger.debug(f"PotatApi: sending {method} request to {url}, {params=}, {json=}")

        response = requests.request(method, url, headers=self.headers, params=params, json=json)

        try:
            data: dict = response.json()
            logger.debug(f"PotatApi: response data: {data}")
        except requests.exceptions.JSONDecodeError:
            logger.warning(f"PotatApi: response does not contain valid JSON: {response.text}")
            return False, {"error": "Response does not contain valid JSON"}
        
        if not response.ok:
            logger.error(f"PotatApi: response was not OK ({response.status_code}) for {url}: {data}")

            if response.status_code == 418:
                raise Unauthorized("Invalid PotatBotat token")
            
            data["status"] = response.status_code
            if not data.get("error"):
                data["error"] = "Response was not OK"
            
            return False, data
        
        return True, data
    

    def getUser(self, username: str) -> dict:
        ok, res = self._request("GET", f"/users/{username}")

        return res["data"][0] if ok else {}


    def execute(self, message: str, cooldownRetries: int = 3) -> tuple[bool, dict]:
        if not message.lower().startswith("@potatbotat"):
            message = "@potatbotat " + message

        json = {"text": message}
        ok, res = self._request("POST", "/execute", json=json)

        if not ok:
            return False, res
        
        data: dict[str, str] = res["data"]
        result: dict = {}

        error: str = data.get("error", "")
        if error and (message.endswith("steal") and ("\u274c" not in error or "[-" in error)): # a failed steal returns an error, which contains the X emoji
            logger.warning(f"PotatApi: execute error: {data=}")

            if not result.get("text"):
                result["text"] = error
            
            if error.endswith("on cooldown.") and cooldownRetries > 0:
                cooldownRetries -= 1
                return self.execute(message, cooldownRetries=cooldownRetries)
            
            return False, result
        
        data["text"] = data["text"].strip("\u034f").strip("¾").strip()

        if data["text"].startswith("\u270b\u23f0") or "ryanpo1Bwuh \u23f0" in data["text"]:
            logger.warning(f"PotatApi: tried to execute farming command on cooldown: {data=}")
            return False, data
        
        return True, data
        
        
    def setToken(self, token: str) -> None:
        self.headers["Authorization"] = f"Bearer {token}"
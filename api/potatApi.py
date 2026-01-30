from .apiClient import ApiClient
from logger import logger



class PotatApi(ApiClient):
    def __init__(self) -> None:
        self.name: str = "PotatApi"
        self.url: str = "https://api.potat.app"
        self.headers: dict[str, str] = {
            "Content-Type": "application/json"
        }
    

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
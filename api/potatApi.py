from .apiClient import ApiClient
from config import config
from logger import logger



class PotatApi(ApiClient):
    def __init__(self) -> None:
        self.name: str = "PotatApi"
        self.url: str = "https://api.potat.app"
        self.headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "PotatBotatBot",
            "Authorization": f"Bearer {config.potatToken}"
        }
    

    def getUser(self, username: str) -> tuple[bool, dict]:
        ok, res = self._request("GET", f"/users/{username}")

        return ok, (res["data"][0] if ok else res)


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
        if error: 
            # a failed steal returns an error, which contains the X emoji (\u274c) or the => unicode char (\u21d2)
            if message.endswith("steal") and ("\u274c" in error or "\u21d2" in error):
                data["text"] = error
            
            else:
                logger.warning(f"PotatApi: execute error: {data=}")

                if not result.get("text"):
                    result["text"] = error
                
                if error.endswith("on cooldown.") and cooldownRetries > 0:
                    cooldownRetries -= 1
                    return self.execute(message, cooldownRetries=cooldownRetries)
                
                return False, result
        
        data["text"] = data.get("text", "Response returned no text")
        data["text"] = data["text"].strip("\u034f").strip("¾").strip()
        data["text"] = data["text"].removesuffix("●").strip()
        
        if data["text"].startswith("\u270b\u23f0") or "ryanpo1Bwuh \u23f0" in data["text"]:
            logger.warning(f"PotatApi: tried to execute farming command on cooldown: {data=}")
            return False, data
        
        return True, data


    def getSelf(self) -> tuple[str, str]:
        ok, res = self.execute("user")

        if not ok:
            logger.critical(f"PotatApi: failed to get self: {res=}")
            raise Exception(f"Failed to get self: {res.get("text", res)}")
        
        parts: list[str] = res["text"].split("●", 2)

        username = parts[0].strip().removeprefix("@").lower()
        userId = parts[1].split("ID: ", 1)[1]

        return username, userId
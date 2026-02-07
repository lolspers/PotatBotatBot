import requests

from .exceptions import Unauthorized
from logger import logger



class ApiClient:
    def __init__(self) -> None:
        self.name: str = "ApiClient"
        self.url: str = ""
        self.headers: dict[str, str] = {}


    def _request(self, method: str, endpoint: str, params: dict | None = None, json: dict | None = None) -> tuple[bool, dict]:
        url = self.url + endpoint
        logger.debug(f"{self.name}: sending {method} request to {url}, {params=}, {json=}")

        response = requests.request(method, url, headers=self.headers, params=params, json=json)

        try:
            data: dict = response.json()
            logger.debug(f"{self.name}: response data: {data}")
        except requests.exceptions.JSONDecodeError:
            logger.warning(f"{self.name}: response does not contain valid JSON: {response.text}")
            return False, {"error": "Response does not contain valid JSON"}
        
        if not response.ok:
            logger.error(f"{self.name}: response was not OK ({response.status_code}) for {url}: {data}")

            if response.status_code == 401:
                raise Unauthorized(f"{self.name}: Invalid token")
            if response.status_code == 418:
                raise Unauthorized("Invalid PotatBotat token")
            
            data["status"] = response.status_code
            if not data.get("error"):
                data["error"] = "Response was not OK"
            
            return False, data
        
        return True, data
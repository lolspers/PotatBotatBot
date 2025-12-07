import requests


def generateToken(clientSecret: str, clientId: str, code: str) -> dict:
    requestData: dict = {
        "client_secret": clientSecret,
        "client_id": clientId,
        "code": code,
        "redirect_uri": "http://localhost",
        "grant_type": "authorization_code"
    }
    
    response = requests.post("https://id.twitch.tv/oauth2/token", data=requestData)

    data: dict = response.json()

    if response.status_code != 200:
        return {"error": data}
    
    scopes: list[str] = data["scope"]

    if "user:write:chat" not in scopes:
        return {"error": {"status": 200, "message": "Token is missing the `user:write:chat` scope"}}
    
    return data



def validateToken(token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get("https://id.twitch.tv/oauth2/validate", headers=headers)

    if response.status_code != 200:
        return {"status": response.status_code, "error": "Invalid OAuth token"}
    
    data: dict = response.json()

    scopes: list[str] = data["scopes"]

    if "user:write:chat" not in scopes:
        return {"status": 200, "error": "Token is missing the `user:write:chat` scope"}
    
    return data
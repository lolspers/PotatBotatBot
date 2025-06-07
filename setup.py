import requests, json

def getTokenDetails(code, secret, redirect, clientId) -> str:
    response = requests.post(f"https://id.twitch.tv/oauth2/token", data={
        "client_id": clientId, 
        "client_secret": secret, 
        "code": code, 
        "grant_type": "authorization_code", 
        "redirect_uri": redirect
    })

    if response.status_code != 200:
        return f"\nFailed to generate token, please try again later ({response.status_code}): {response.json()}"
    
    else:
        data = response.json()
            
        global config
        config.update({"twitchToken": data["access_token"]})
        config.update({"clientId": clientId})
        config.update({"refreshToken": data["refresh_token"]})
        config.update({"clientSecret": secret})

        return "Generated token"

def getUserIds(usernames: list) -> str | dict:
    url = "https://api.twitch.tv/helix/users"
    params = []
    for user in usernames:
        params.append(f"login={user}")
    params = "?"+"&".join(params)
    response = requests.get(url + params, headers={"Authorization": f"Bearer {config["twitchToken"]}", "Client-Id": config["clientId"]})
    if response.status_code != 200:
        return f"Failed to get user ids: {response.json()}"
    
    data = response.json()["data"]
    userIds = {}
    for user in data:
        userIds.update({user["login"]: user["id"]})

    return userIds



try:
    with open("config.json", "r") as file:
        config = json.loads(file.read())
except FileNotFoundError:
    config = {}



if config.get("potatToken") and input("You already have a potatbotat token set, do you want to update it? (y/n) ").lower() != "y": pass
else:
    print("Copy your potatbotat token on https://potat.app > f12 > storage > local storage > https://potat.app > authorization")
    potatToken = input("PotatBotat token: ")

    config.update({"potatToken": potatToken})



if config.get("twitchToken") and config.get("clientId") and config.get("refreshToken") and config.get("clientSecret") and input("You already have twitch token details set, do you want to update them? (y/n) ").lower() != "y": pass
else:
    print("\nOn https://dev.twitch.tv/console/apps go to your application")
    print("Under the name copy one of the OAuth Redirect URLs")
    redirect = input("Redirect URL: ")

    print("\nScroll down and click on 'New Secret'")
    secret = input("Client secret: ").strip().lower()
    if len(secret) != 30:
        while len(secret) != 30:
            print("Invalid client secret")
            secret = input("Client secret: ").strip().lower()

    print("\nAbove the secret copy the Client ID")
    clientId = input("Client ID: ")
    if len(clientId) != 30:
        while len(clientId) != 30:
            print("Invalid client id")
            clientId = input("Client ID: ").strip().lower()

    print(f"\nGo to https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={clientId}&redirect_uri={redirect}&scope=user:write:chat")
    print("From the URL bar copy the code in between 'code=' and '&scope'")

    code = input("Code: ").strip().lower()
    if len(code) != 30:
        while len(code) != 30:
            print("Invalid code")
            code = input("Code: ").strip().lower()

    print("\nGenerating token...")
    result = getTokenDetails(code, secret, redirect, clientId)
    print(result)
    if result != "Generated token":
        with open("config.json", "w") as file:
            json.dump(config, file, indent=4)
            
            print("Updated")
        input("\nPress enter to exit")



if config.get("username") and config.get("userId") and config.get("channelId") and input("You already have you username and channel set, do you want to update them? (y/n) ") != "y": pass
else:
    username = input("\nYour twitch username: ").strip().replace("#", "", 1).replace("@", "", 1).lower()
    channel = input("Channel you want to farm in: ").strip().replace("#", "", 1).replace("@", "", 1).lower()

    userIds = getUserIds([username, channel])
    if not isinstance(userIds, dict):
        print(userIds)

    else:
        config.update({"username": username})
        config.update({"userId": userIds[username]})
        config.update({"channelId": userIds[channel]})



with open("config.json", "w") as file:
    json.dump(config, file, indent=4)
    
    print("Successfully updated config")

input("\nPress enter to exit")
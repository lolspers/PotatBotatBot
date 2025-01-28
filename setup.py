import requests, json

with open("config.json", "r") as file:
    config = json.loads(file.read())

def getTokenDetails(code, secret, redirect, clientId, potatToken) -> str:
    response = requests.post(f"https://id.twitch.tv/oauth2/token", data={
        "client_id": clientId, 
        "client_secret": secret, 
        "code": code, 
        "grant_type": "authorization_code", 
        "redirect_uri": redirect})
    if response.status_code != 200:
        return f"\nFailed to generate token ({response.status_code}): {response.text}"
    
    else:
        data = response.json()
            
        config["potatToken"] = potatToken
        config["twitchToken"] = data["access_token"]
        config["clientId"] = clientId
        config["refreshToken"] = data["refresh_token"]
        config["clientSecret"] = secret

        with open("config.json", "w") as file:
            json.dump(config, file, indent=4)

        return "Generated token and updated config"

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

updatePotat = True
updateTwitch = True
updateUser = True

if config["potatToken"] != "":
    if input("You already have a potatbotat token set, do you want to update it? (y/n) ").lower() != "y":
        updatePotat = False

if updatePotat:
    print("Copy your potatbotat token on https://potat.app > f12 > storage > local storage > https://potat.app > authorization")
    potatToken = input("PotatBotat token: ")


if config["twitchToken"] != "" and config["clientId"] != "" and config["refreshToken"] != "" and config["clientSecret"] != "":
    if input("You already have twitch token details set, do you want to update them? (y/n) ").lower() != "y":
        updateTwitch = False

if updateTwitch:
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
    print("From the URL bar copy the code after 'code=' and until '&scope' (the unable to connect doesn't matter)")

    code = input("Code: ").strip().lower()
    if len(code) != 30:
        while len(code) != 30:
            print("Invalid code")
            code = input("Code: ").strip().lower()

    print("\nGenerating token...")
    print(getTokenDetails(code, secret, redirect, clientId, potatToken))


if config["username"] != "" and config["userId"] != "" and config["95676405"] != "":
    if input("You already have you username and channel set, do you want to update them? (y/n) ") != "y":
        updateUser = False

if updateUser:
    username = input("\nYour twitch username: ").strip().replace("#", "", 1).replace("@", "", 1).lower()
    channel = input("Channel you want to farm in: ").strip().replace("#", "", 1).replace("@", "", 1).lower()

    userIds = getUserIds([username, channel])
    if not isinstance(userIds, dict):
        print(userIds)

    else:
        config["username"] = username
        config["userId"] = userIds[username]
        config["channelId"] = userIds[channel]

        with open("config.json", "w") as file:
            json.dump(config, file, indent=4)
        print("Successfully updated config")

input("\nPress enter to exit")
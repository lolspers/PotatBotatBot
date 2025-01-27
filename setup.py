import requests, json

def getTokenDetails(code, secret, redirect, clientId, potatToken):
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

        with open("config.json", "r") as file:
            config = json.loads(file.read())
            
        config["potatToken"] = potatToken
        config["twitchToken"] = data["access_token"]
        config["clientId"] = clientId
        config["refreshToken"] = data["refresh_token"]
        config["clientSecret"] = secret

        with open("config.json", "w") as file:
            json.dump(config, file, indent=4)

        return "Generated token and updated config"


print("Copy your potatbotat token on https://potat.app > f12 > storage > local storage > https://potat.app > authorization")
potatToken = input("PotatBotat token: ")

print("On https://dev.twitch.tv/console/apps go to your application")
print("Under the name copy one of the OAuth Redirect URLs")
redirect = input("Redirect URL: ")

print("Scroll down and click on 'New Secret'")
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

print("Generating token...")
print(getTokenDetails(code, secret, redirect, clientId, potatToken))

input("\nPress enter to exit")
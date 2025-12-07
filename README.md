# PotatBotatBot
A bot for automating [PotatBotat](https://potat.app) farming commands.


## Installation
Make sure you have [python](https://www.python.org/downloads/) 3.12 or later installed.

### Cloning
Clone the repository in a terminal like powershell.
```bash
git clone https://github.com/lolspers/PotatBotatbot.git
```

Cd into the cloned repo.

```bash
cd PotatBotatBot
```

Install the required packages.
```bash
pip install -r requirements.txt
```

### Configuration
Copy `example-config.json`, rename it to `config.json` and open it in any text editor.

Set `username` to your twitch username and `channel` to the channel you want to farm in (when farming through twitch).

#### PotatBotat

Sign in on [potat.app](https://potat.app). Press `Ctrl + Shift + I` and to go the console. Copy `localStorage.getItem("authorization")` and paste it in the console. Copy the text that it returns. In `config.json` set `potatToken` to the text you just copied. 

> [!TIP]
> You might need to type `allow pasting` in your console before you can paste code in it.

> [!NOTE]
> It's not required for PotatBotat to be joined in your channel, but it is still recommended to do so.

#### Twitch

> [!TIP]
> If you're only going to farm through potatbotat api, none of the following twitch configuration is required.

Register an application [here](https://dev.twitch.tv/console/apps) and give it any name. Set `OAuth Redirect URLs` to `http://localhost`, `Category` to `Other`, and `Client Type` to `Confidential`.

Create the application and click on its `Manage` button.

Click `New Secret` and copy it. In `config.json` set `clientSecret` to the Client Secret you just copied and set `clientId` to the Client ID.

Copy the following link and set `client_id` to your applications Client ID.
`https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=<CLIENT ID HERE>&redirect_uri=http://localhost&scope=user:write:chat`

Open the link in any browser and authorize the app on the account you want to farm on. You should be redirected to a link similar to `http://localhost/?code=gulfwdmys5lsm6qyz4xiz9q32l10&scope=user%3Awrite%3Achat`.

Copy the code from the link and in `config.json` set `authCode` to the code you just copied.

`twitchToken` and `refreshToken` should automatically be generated on first start.


> [!IMPORTANT]
> Any changes made to `config.py` while the bot is running will most likely be overwritten, as the file is only read on start.


## Usage

To start the bot simply open `main.py`.
Any errors will be logged in `logs.log`.
# PotatBotatBot
A bot for automating [PotatBotat](https://potat.app) farming commands. Supports execution through both Twitch chat and PotatBotat API. Configurable which commands and shop items to automate.

## Installation
> [Python](https://www.python.org/downloads/) 3.12 or later is required.

In a terminal, clone the repository, create a virtual environment and install the required packages.

#### Windows
```bash
git clone https://github.com/lolspers/PotatBotatBot.git
cd PotatBotatBot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### Linux/macOS
```bash
git clone https://github.com/lolspers/PotatBotatBot.git
cd PotatBotatBot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Rename `example-config.json` to `config.json` and open it in any text editor.

#### PotatBotat

Sign in on [potat.app](https://potat.app). Open the browser console and run:

```js
localStorage.getItem("authorization")
```

Copy the returned value and paste it as `potatToken` in `config.json`.

> [!NOTE]
> It's not required for PotatBotat to be joined in your channel, but it is still recommended to do so.

#### Twitch

> [!TIP]
> If you're only going to farm through potatbotat api, none of the following twitch configuration is required.

In `config.json` set `channelId` to the user id of the channel you want to send the messages to. One way to get a user id, is by using the [user command](https://potat.app/help/user).

Register an application [here](https://dev.twitch.tv/console/apps) and give it any name. Set `OAuth Redirect URLs` to `http://localhost`, `Category` to `Other`, and `Client Type` to `Confidential`.

Create the application and click on its `Manage` button.

Click `New Secret` and copy it. In `config.json` set `clientSecret` to the Client Secret you just copied and set `clientId` to the Client ID.

Copy the following link and set `client_id` to your applications Client ID.
`https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=<CLIENT ID HERE>&redirect_uri=http://localhost&scope=user:write:chat`

Open the link in any browser and authorize the app on the account you want to farm on. You should be redirected to a link similar to `http://localhost/?code=gulfwdmys5lsm6qyz4xiz9q32l10&scope=user%3Awrite%3Achat`.

Copy the code from the link and in `config.json` set `authCode` to the code you just copied.

`twitchToken` and `refreshToken` should automatically be generated on first start.

> [!IMPORTANT]
> Any changes made to `config.json` while the bot is running will most likely be overwritten, as the file is only read on start.

### Optional settings

| Setting | Data type | Description | Default |
| ------- | --------- | ----------- | ------- |
| `printInColor` | bool | If true, prints text in the console in a certain color, based on the type of message. | `true` |
| `printTime` | bool | If true, prepends the time to text printed in the console. (`[HH:MM:SS]`) | `true` |
| `usePotatApi` | bool | If true, executes commands through [PotatBotat api](https://potat.app/api/docs) instead of executing it through twitch chat. | `false` |
| `farmingCommands` | dict[str, bool] | Commands set to `true` will be automated. | <details> `{ "potato": true, "steal": true, "trample": false, "cdr": true, "quiz": false }` </details> |
| `shopItems` | dict[str, bool] | Shop items set to `true` will be automated. These will only be bought right after or before the command they affect has been executed. | <details> `{ "shop-fertilizer": true, "shop-guard": true, "shop-cdr": true, "shop-quiz": false }` </details> |
| `loggingLevel` | int | The level threshold of the logger. Allowed values are: 0 (NOTSET), 10 (DEBUG), 20 (INFO), 30 (WARNING), 40 (ERROR), 50 (CRITICAL). | `30` |

> [!WARNING]
> Any settings not mentioned above should not be modified.

### Example config

```json
{
    "channelId": "123456789",
    "channelPrefix": "",
    "twitchToken": "",
    "refreshToken": "",
    "clientId": "COPY_TWITCH_CLIENT_ID_HERE",
    "clientSecret": "COPY_TWITCH_CLIENT_SECRET_HERE",
    "authCode": "COPY_AUTH_CODE_HERE",
    "potatToken": "COPY_POTAT_TOKEN_HERE",
    "printInColor": true,
    "printTime": true,
    "usePotatApi": false,
    "farmingCommands": {
        "potato": true,
        "steal": true,
        "trample": false,
        "cdr": true,
        "quiz": false
    },
    "shopItems": {
        "shop-fertilizer": true,
        "shop-guard": true,
        "shop-cdr": true,
        "shop-quiz": false
    },
    "loggingLevel": 30
}
```

## Usage

To start the bot simply run `main.py`.

#### Windows
```bash
.venv\Scripts\activate
python main.py
```

#### Linux
```bash
source .venv/bin/activate
python3 main.py
```

Any errors will be logged in `logs.log`.

## Help

For any help or support, make an issue [here](https://github.com/lolspers/PotatBotatBot/issues), or contact me on [discord](https://discord.com/users/518308474828881930) or [twitch](https://www.twitch.tv/lolspers).

## Contributing

Pull requests and issues are welcome.

## License

This project is licensed under the MIT License.  
See the [LICENSE](https://github.com/lolspers/PotatBotatBot/blob/main/LICENSE) file for details.
# PotatBotatBot
A bot for automating [PotatBotat](https://potat.app) farming commands.

## Installation
Make sure you have [python](https://www.python.org/downloads/) (at least 3.12) and the [requests](https://pypi.org/project/requests/) module installed.
```bash
pip install requests
```

Clone the repository in a terminal like powershell.
```bash
git clone https://github.com/lolspers/PotatBotatbot
```

Make (or use an existing) [application](https://dev.twitch.tv/console/apps) and set Client Type to Confidential.
If you don't have a website for the redirect URL you can set it to `http://localhost`.

Open `setup.py` and follow the steps, this will set the config for you, or edit example-config.json manually and rename it to config.json if you know what you're doing.

An error can sometimes occur when PotatBotat is not joined in your channel, you can prevent this by adding PotatBotat [here](https://potat.app/).

To start the bot simply open `main.py`.
Any errors should get logged in `logs.txt`.
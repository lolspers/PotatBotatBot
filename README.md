# PotatBotatBot
A bot for automating [PotatBotat](https://potat.app) farming commands.

## Installation
Make sure you have [python](https://www.python.org/downloads/) (at least 3.12).

Clone the repository in a terminal like powershell.
```bash
git clone https://github.com/lolspers/PotatBotatbot.git
```

Cd into the cloned repo

```bash
cd PotatBotatBot
```

Install the required packages
```bash
pip install -r requirements.txt
```


Make (or use an existing) [application](https://dev.twitch.tv/console/apps) and set Client Type to Confidential.
If you don't have a website for the redirect URI you can set it to `http://localhost`.

Open `setup.py` and follow the steps, this will set the config for you, or edit example-config.json manually and rename it to config.json if you know what you're doing.

An error can sometimes occur when PotatBotat is not joined in your channel, you can prevent this by adding PotatBotat [here](https://potat.app/).

To start the bot simply open `main.py`.
Any errors will be logged in `logs.log`.
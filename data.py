from time import strftime
import json
from os import _exit

def log(message) -> None:
    with open("logs.txt", "a+", encoding="utf-8") as file:
        file.write(f"\n [{strftime("%Y-%m-%d %H:%M:%S")}] {str(message)}")

def getConfig():
    try:
        with open("config.json", "r") as file:
            return json.loads(file.read())
    except FileNotFoundError:
        input("Please set up config.json or run setup.py before starting the bot")
        _exit(1)

def updateConfig(data):
    with open("config.json", "w") as file:
        json.dump(data, file, indent=4)
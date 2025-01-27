from time import strftime
import json

def log(message) -> None:
    with open("logs.txt", "a+", encoding="utf-8") as file:
        file.write(f"\n [{strftime("%Y-%m-%d %H:%M:%S")}] {str(message)}")

def getConfig():
    with open("config.json", "r") as file:
        return json.loads(file.read())

def updateConfig(data):
    with open("config.json", "w") as file:
        json.dump(data, file, indent=4)
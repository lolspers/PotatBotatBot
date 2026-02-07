import os
import logging
import colorama
from datetime import datetime
from emoji import emojize as _emojize, demojize as _demojize

from config import config


killedProgram: bool = False

logger = logging.getLogger("logger")

fileHandler = logging.FileHandler("logs.log", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
fileHandler.setFormatter(formatter)

logger.addHandler(fileHandler)
logger.setLevel(config.loggingLevel)


colorama.init(autoreset=True)



def demojize(text: str, escape: bool = False) -> str:
    if escape:
        text = ascii(_demojize(text))
    
    return _emojize(text) if config.printEmojis else _demojize(text)



def tprint(*values, time: bool = True):
    result = []
    for value in values:
        result.append(demojize(value) if isinstance(value, str) else value)

    values = tuple(result)

    if config.printTime and time:
        dt = datetime.now().strftime("[%H:%M:%S]")

        if config.printColor:
            dt = colorama.Style.DIM + dt

        values = (dt,) + values

    print(*values)



def cprint(text, fore: str | None = None, style: str | None = None, back: str | None = None, time: bool = True):
    if config.printColor:
        ansi = ""

        if fore:
            ansi += fore

        if style:
            ansi += style

        if back:
            ansi += back

        text = ansi + str(text)
    
    
    tprint(text, time=time)



def clprint(*values, fore: list[str | None] | None = None, style: list[str | None] | None = None, back: list[str | None] | None = None, globalFore: str = "", globalStyle: str = "", globalBack: str = "", time: bool = True):
    if config.printColor:
        values = list(values)

        for type in [fore, style, back]:
            if not type:
                continue

            for i in range(len(type)):
                ansi = type[i]

                if ansi and i < len(values):
                    values[i] = f"{ansi}{values[i]}"


        globalAnsi = globalFore + globalStyle + globalBack

        if globalAnsi:
            values = [globalAnsi + str(value) for value in values]
    

    tprint(*values, time=time)



def killProgram() -> None:
    global killedProgram
    killedProgram = True
    
    cprint("\nPress enter to exit...", style=colorama.Style.DIM, time=False)

    input()

    os._exit(0)
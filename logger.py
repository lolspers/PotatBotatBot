import os
import logging
import colorama

from datetime import datetime


logger = logging.getLogger("logger")

fileHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
fileHandler.setFormatter(formatter)

logger.addHandler(fileHandler)
logger.setLevel(30)


colorama.init(autoreset=True)

printColors: bool = True
printTime: bool = True



def setPrintColors(enable: bool) -> None:
    global printColors

    printColors = enable


def setPrintTime(enable: bool) -> None:
    global printTime

    printTime = enable



def tprint(*values, time: bool = True):
    if printTime and time:
        dt = datetime.now().strftime("[%H:%M:%S]")

        if printColors:
            dt = colorama.Style.DIM + dt

        values = (dt,) + values

    print(*values)



def cprint(text, fore: str | None = None, style: str | None = None, back: str | None = None, time: bool = True):
    if printColors:
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
    if printColors:
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
    cprint("\nPress enter to exit...", style=colorama.Style.DIM, time=False)

    input()

    os._exit(1)
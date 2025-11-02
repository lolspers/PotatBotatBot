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
printDates: bool = True



def setPrintColors(enable: bool) -> None:
    global printColors

    printColors = enable


def setPrintDates(enable: bool) -> None:
    global printDates

    printDates = enable



def dprint(*values, date: bool = True):
    if printDates and date:
        dt = datetime.now().strftime("[%m-%d %H:%M:%S]")

        if printColors:
            dt = colorama.Style.DIM + dt

        values = (dt,) + values

    print(*values)



def cprint(text, fore: str | None = None, style: str | None = None, back: str | None = None, date: bool = True):
    if printColors:
        ansi = ""

        if fore:
            ansi += fore

        if style:
            ansi += style

        if back:
            ansi += back

        text = ansi + str(text)
    
    
    dprint(text, date=date)



def clprint(*values, fore: list[str | None] | None = None, style: list[str | None] | None = None, back: list[str | None] | None = None, globalFore: str = "", globalStyle: str = "", globalBack: str = "", date: bool = True):
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
    

    dprint(*values, date=True)



def killProgram() -> None:
    cprint("\nPress enter to exit...", style=colorama.Style.DIM, date=False)

    input()

    os._exit(1)
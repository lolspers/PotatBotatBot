import os
import logging
import colorama


logger = logging.getLogger("logger")

fileHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
fileHandler.setFormatter(formatter)

logger.addHandler(fileHandler)
logger.setLevel(30)


colorama.init(autoreset=True)

printColors: bool = True



def setPrintColors(enable: bool) -> None:
    global printColors

    printColors = enable



def cprint(text, fore: str | None = None, style: str | None = None, back: str | None = None):
    if not printColors:
        print(text)
        return


    ansi = ""

    if fore:
        ansi += fore

    if style:
        ansi += style

    if back:
        ansi += back
    
    
    print(ansi + str(text))



def clprint(*values, fore: list[str | None] | None = None, style: list[str | None] | None = None, back: list[str | None] | None = None, globalFore: str = "", globalStyle: str = "", globalBack: str = ""):
    if not printColors:
        print(*values)
    
    
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
        values = [globalAnsi + value for value in values]

    print(*values)



def killProgram() -> None:
    cprint("\nPress enter to exit...", style=colorama.Style.DIM)

    input()

    os._exit(1)
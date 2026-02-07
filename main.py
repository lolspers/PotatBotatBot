from colorama import Fore, Style, Back
from os import _exit
from time import sleep
from traceback import print_exc

from logger import logger, cprint, clprint, killProgram
try:
    from classes.user import User
    from config.inputs import Inputs
    from exceptions import StopBot

except Exception as e:
    logger.critical("Error while importing in main", exc_info=e)
    clprint(f"{type(e).__name__}:", str(e), style=[Style.DIM], globalFore=Fore.MAGENTA)
    _exit(1)


def main() -> None:
    try:
        logger.debug("Started")
        
        user = User()
        inputs = Inputs(user)

        user.setCooldowns()

    except Exception as e:
        logger.critical("Error while initializing User/Inputs", exc_info=e)
        print_exc()
        clprint(f"{type(e).__name__}:", str(e), style=[Style.DIM], globalFore=Fore.MAGENTA)
        killProgram()


    while True:
        try:
            if not inputs.queue.empty():
                uInput = inputs.queue.get()

                if uInput in ["s", "stop"]:
                    killProgram()

            
            user.executeCommands()

            if user.executions > 15:
                logger.warning("Reached execution limit")
                user.executions = 0
                cprint(f"Paused for 3 hours - Too many executions in a short period of time", fore=Fore.YELLOW)
                sleep(3600 * 3)
                cprint("Resumed", fore=Fore.CYAN)
                logger.info("Continued after execution limit")

            if user.executions > 0:
                user.executions -= 0.1


            sleep(5)

        
        except StopBot as e:
            logger.critical(f"Stopped bot", exc_info=e)
            clprint("Stopped bot:", str(e), style=[Style.DIM], globalFore=Fore.MAGENTA)
            killProgram()


        except KeyboardInterrupt as e:
            logger.info("KeyboardInterrupt")
            _exit(0)


        except Exception as e:
            logger.error("Exception in main", exc_info=e)
            clprint(f"{type(e).__name__}:", str(e), style=[Style.DIM], globalFore=Fore.RED)
            sleep(15)



if __name__ == "__main__":
    main()
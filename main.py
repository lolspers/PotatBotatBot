import sys
from time import sleep

from colorama import Fore, Style

import globals as g

try:
    from classes.user import User
    from config.inputs import Inputs
    from exceptions import StopBot

except Exception as e:
    g.logger.critical("Error while importing in main", exc_info=e)
    sys.exit(1)


inputs: Inputs | None = None


def killProgram() -> None:
    if inputs and inputs.active:
        inputs.active = False

    g.logger.info("Killed program")
    g.logger.info("\nPress enter to exit...",
                  extra={"color": Style.DIM, "print": True, "write": False})

    input()
    sys.exit(0)


def main() -> None:
    try:
        g.config = g.config

        g.logger.debug("Started")

        user = User()
        inputs = Inputs(user)

        user.setCooldowns()

    except Exception as e:
        g.logger.critical("Error while initializing User/Inputs", exc_info=e)
        return killProgram()


    while True:
        try:
            if not inputs.queue.empty():
                uInput = inputs.queue.get()

                if uInput in ["s", "stop"]:
                    return killProgram()


            user.executeCommands()

            if user.executions > 15:
                user.executions = 0
                g.logger.warning("Reached execution limit")
                g.logger.warning(
                    "Paused for 3 hours - Too many executions in a short period of time")
                sleep(3600 * 3)
                g.logger.info("Resumed after execution limit", extra={"color": Fore.CYAN})

            if user.executions > 0:
                user.executions -= 0.1


            sleep(5)


        except StopBot as e:
            g.logger.critical("Stopped bot:", exc_info=e)
            killProgram()


        except KeyboardInterrupt:
            g.logger.debug("KeyboardInterrupt")
            sys.exit(0)


        except Exception as e:
            g.logger.error("Exception in main:", exc_info=e)
            sleep(15)



if __name__ == "__main__":
    main()

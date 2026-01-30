
from colorama import Fore, Style
from time import time, sleep

from config import config
from logger import logger, cprint, clprint
from utils import shopItemPrice, quizes
from exceptions import StopBot
from . import potat, twitch
from .exceptions import Unauthorized


lastChannelPrefixCheck = 0



def buyItem(item: str, rank: int, potatoes: int) -> bool:
    price = shopItemPrice(item=item, rank=rank)

    if potatoes < price:
        return False
    

    ok, data = send(f"shop {item}")

    if ok:
        print(f"Bought shop item: {data}")

    else:
        print(Fore.RED + f"Failed to buy shop item: {data}")

    return True



def executeQuiz() -> None:
    # first send the quiz in twitch chat,
    # to make potat send the quiz completion message in the right chat
    if not config.usePotat:
        ok, response = send("quiz")
        cprint(response, fore=(None if ok else Fore.RED))
        sleep(5.5)


    for n in range(3):
        ok, res = potat.execute("quiz")
        quiz: str = res.get("text", "")

        if ok:
            break

        if "forgot: " in quiz:
            quiz = quiz.split("forgot: ", 1)[1]
            break

        sleep(5.5)

    if not ok:
        logger.warning(f"Failed to get quiz: {quiz}")
        clprint("Failed to get quiz:", quiz, style=[Style.BRIGHT], globalFore=Fore.RED)
        return
    
    quiz = quiz.removesuffix("(You have five minutes to answer correctly, time starts now!)").strip()


    clprint("Received quiz:", quiz, style=[None, Style.DIM])
    answer = quizes.get(quiz, None)

    if answer is None:
        logger.warning(f"No quiz anser found for quiz: {quiz}")
        clprint("No quiz answer found for quiz:", quiz, style=[Style.BRIGHT], globalFore=Fore.RED)
        return

    clprint("Found quiz answer:", answer, style=[Style.BRIGHT])

    sleep(5.5)
    ok, response = send(f"a {answer}")

    if not ok:
        clprint("Failed to answer quiz:", response, style=[None, Style.DIM])
    else:
        clprint("Answered quiz:", response, style=[None, Style.DIM], globalFore=Fore.GREEN)



def checkChannelPrefix() -> None:
    channel = twitch.getUser(config.channelId).get("login")

    if not channel:
        raise StopBot(f"Tried to check channel prefix, but the channel id is invalid ({config.channelId})")

    data: dict = potat.getUser(channel)
    channelData: dict | None = data.get("channel")

    if not channelData:
        raise StopBot(f"Failed to get channel prefix: PotatBotat is not joined in #{channel}")
    
    prefix = channelData["settings"]["prefix"]

    if config.channelPrefix != prefix:
        config.updateChannelPrefix(prefix)

        logger.info(f"Updated channel prefix: {prefix=}")
        print(Style.DIM + Fore.CYAN + f"Updated channel prefix to '{prefix}'")

        global lastChannelPrefixCheck
        lastChannelPrefixCheck = time()



def send(message: str, forcePotat: bool = False, forceTwitch: bool = False, prefix: bool = True) -> tuple[bool, str]:
    if (config.usePotat and not forceTwitch) or forcePotat:
        ok, res = potat.execute(message)

        return ok, res.get("text", res.get("error", res))


    else:
        if prefix:
            if time() > lastChannelPrefixCheck + 3600:
                try:
                    channelData = twitch.getUser(config.channelId)

                except Unauthorized:
                    twitch.refreshAccessToken()

                    channelData = twitch.getUser(config.channelId)

                if not channelData:
                    raise StopBot("The provided channel id was not found!")
                
                checkChannelPrefix()

            message = config.channelPrefix + message

        
        try:
            ok, res = twitch.send(channelId=config.channelId, message=message)
            return ok, message if ok else f"Failed to send twitch message: {res}"
        
        except Unauthorized:
            twitch.refreshAccessToken()

            ok, res = twitch.send(channelId=config.channelId, message=message)
            return ok, message if ok else f"Failed to send twitch message: {res}"
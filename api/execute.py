
from colorama import Fore, Style
from time import time, sleep

from config import config
from logger import logger, cprint, clprint
from utils import shopItemPrice, quizes
from exceptions import StopBot
from .exceptions import Unauthorized
from .potat import potatSend, getChannelPrefix, lastChannelPrefixCheck
from .twitch import twitchSend, getTwitchUser, refreshToken as refreshTwitchToken



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
    # first execute the quiz in the targetted twitch chat
    # to not send the quiz completion message in your own chat
    if not config.usePotat:
        ok, response = send("quiz")
        cprint(response, fore=(None if ok else Fore.RED))
        sleep(5) # quiz cooldown


    ok, quiz = potatSend("quiz", cdRetries=3)

    if not ok:
        logger.warning(f"Failed to get quiz: {quiz}")
        clprint("Failed to get quiz:", quiz, style=[Style.BRIGHT], globalFore=Fore.RED)
        return

    clprint("Received quiz:", quiz, style=[None, Style.DIM])
    answer = quizes.get(quiz, None)

    if answer is None:
        logger.warning(f"No quiz anser found for quiz: {quiz}")
        clprint("No quiz answer found for quiz:", quiz, style=[Style.BRIGHT], globalFore=Fore.RED)
        return

    clprint("Found quiz answer:", answer, style=[Style.BRIGHT])

    sleep(6) # small cooldown to be safe
    ok, response = send(f"a {answer}")

    if not ok:
        clprint("Failed to answer quiz:", response, style=[None, Style.DIM])
    else:
        clprint("Answered quiz:", response, style=[None, Style.DIM], globalFore=Fore.GREEN)



def checkChannelPrefix() -> None:
    channel = getTwitchUser(config.channelId).get("login")

    if not channel:
        raise StopBot(f"Tried to check channel prefix, but the channel id is invalid ({config.channelId})")

    prefix = getChannelPrefix(channel)

    if config.channelPrefix != prefix:
        config.updateChannelPrefix(prefix)

        logger.info(f"Updated channel prefix: {prefix=}")
        print(Style.DIM + Fore.CYAN + f"Updated channel prefix to '{prefix}'")

        global lastChannelPrefixCheck
        lastChannelPrefixCheck = time()



def send(message: str, forcePotat: bool = False, forceTwitch: bool = False, prefix: bool = True) -> tuple[bool, str]:
    if (config.usePotat and not forceTwitch) or forcePotat:
        return potatSend(message)


    else:
        if prefix:
            if time() > lastChannelPrefixCheck + 3600:
                try:
                    channelData = getTwitchUser(config.channelId)

                except Unauthorized:
                    data = refreshTwitchToken(clientSecret=config.clientSecret, clientId=config.clientId, refreshToken=config.refreshToken)
                    config.updateTwitchTokens(accessToken=data["accessToken"], refreshToken=data["refreshToken"])


                    channelData = getTwitchUser(config.channelId)

                if not channelData:
                    raise StopBot("The provided channel id was not found!")
                
                checkChannelPrefix()

            message = config.channelPrefix + message

        
        try:
            return twitchSend(channelId=config.channelId, userId=config.userId, message=message)
        
        except Unauthorized:
            refreshTwitchToken(clientSecret=config.clientSecret, clientId=config.clientId, refreshToken=config.refreshToken)
            config.updateTwitchTokens(accessToken=data["accessToken"], refreshToken=data["refreshToken"])

            return twitchSend(channelId=config.channelId, userId=config.userId, message=message)
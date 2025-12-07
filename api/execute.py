
from colorama import Fore, Style
from time import time

from config import config
from logger import logger
from utils import shopItemPrice
from exceptions import StopBot
from .exceptions import Unauthorized
from .potat import potatSend, getChannelPrefix, getUserPrefix, lastChannelPrefixCheck
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



def checkUserPrefix() -> None:
    prefix = getUserPrefix(config.username)

    if prefix != config.userPrefix:
        config.updateUserPrefix(prefix)

        logger.info(f"Updated user prefix: {prefix=}")
        print(Style.DIM + Fore.CYAN + f"Updated user prefix to '{prefix}'")



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
        if prefix:
            message = config.userPrefix + message

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



if not config.userPrefix:
    checkUserPrefix()
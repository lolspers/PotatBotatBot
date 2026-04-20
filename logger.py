from __future__ import annotations

import contextlib
import logging
import queue
import sys
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener
from typing import TYPE_CHECKING

import colorama
import regex as re
import requests
from colorama import Back, Fore, Style
from emoji import demojize, emojize

if TYPE_CHECKING:
    from config import Config


colorama.init(autoreset=True)

logColors = {
    logging.DEBUG: Style.DIM,
    logging.INFO: Fore.WHITE,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA,
}
colors = {
    "Back": Back,
    "Fore": Fore,
    "Style": Style,
}
colorPattern = re.compile(r"(<(Style|Fore|Back)\.([A-Z]+)>)")
dcMdChars = "\\".join("*_~-#[](<>`|")
dcMdPattern = re.compile(fr"\\[{dcMdChars}](*SKIP)|([{dcMdChars}])")


class WebhookHandler(logging.Handler):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.url: str = url


    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg: str = self.format(record)[:2000]

            data = {
                "username": "PotatBotatBot",
                "content": msg,
                "avatar_url": "https://segs.lol/CceppX",
            }

            response = requests.post(self.url, json=data)
            response.raise_for_status()

        except Exception:
            self.handleError(record)



class StreamFormatter(logging.Formatter):
    def __init__(self, config: Config):
        self.config: Config = config

        super().__init__("%(message)s")


    def format(self, record: logging.LogRecord) -> str:
        msg = record.msg

        time = ""
        if self.config.printTime and (getattr(record, "time", None) is not False):
            time = datetime.now().strftime("[%H:%M:%S] ")

        if getattr(record, "escape", None):
            msg = ascii(demojize(msg))[1:-1]

        if self.config.printColor:
            time = Style.DIM + time + Style.NORMAL

            for fullMatch, ansiTypeG, ansiColorG in colorPattern.findall(msg):
                ansi = getattr(colors.get(ansiTypeG), ansiColorG, "")
                msg = msg.replace(fullMatch, ansi, 1)

            ansiColor = getattr(record, "color", None)
            if ansiColor is None:
                ansiColor = logColors.get(record.levelno, Fore.WHITE)

            msg = f"{ansiColor}{msg}"

        else:
            msg = colorPattern.sub("", msg)

        msg = f"{time}{msg}"

        msg = emojize(msg) if self.config.printEmojis else demojize(msg)

        originalMsg = record.msg
        record.msg = msg
        msg = super().format(record)
        record.msg = originalMsg
        return msg


class FileFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)

        data = getattr(record, "data", None)
        if isinstance(data, (dict, list)):
            with contextlib.suppress(TypeError):
                formatted += f"Extra data:\n {data!s}"

        return formatted


class WebhookFormatter(logging.Formatter):
    def __init__(self, config: Config):
        self.config: Config = config

        super().__init__("%(message)s")


    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # discord's ansi sadly isn't fully compatible with colorama
        msg = colorPattern.sub("", msg)
        msg = dcMdPattern.sub(r"\\\g<1>", msg)
        return msg[:2000]



class StreamLevelFilter(logging.Filter):
    def __init__(self, name: str = "", level: int = 30) -> None:
        self.level: int = level
        super().__init__(name=name)


    def filter(self, record: logging.LogRecord) -> bool:
        forcePrint = getattr(record, "print", None)
        if forcePrint is not None:
            return bool(forcePrint)
        return record.levelno >= self.level


class FileFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        forceWrite = getattr(record, "write", None)
        if forceWrite is not None:
            return bool(forceWrite)
        return True


class WebhookFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return bool(getattr(record, "webhook", None))



def getLogger(config: Config) -> logging.Logger:
    logger = logging.getLogger(__name__)

    logQueue = queue.Queue()
    queueHandler = QueueHandler(logQueue)

    fileHandler = logging.FileHandler("logs.log", encoding="utf-8")
    fileHandler.addFilter(FileFilter())
    fileHandler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    fileHandler.setLevel(config.loggingLevel)

    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.addFilter(StreamLevelFilter(level=config.consoleLoggingLevel))
    streamHandler.setFormatter(StreamFormatter(config))
    streamHandler.setLevel(logging.DEBUG)

    if config.webhook:
        webhookHandler = WebhookHandler(config.webhook)
        webhookHandler.addFilter(WebhookFilter())
        webhookHandler.setFormatter(WebhookFormatter(config))
        webhookHandler.setLevel(logging.DEBUG)

        queueListener = QueueListener(
            logQueue,
            webhookHandler,
        )
        queueListener.start()

    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    logger.addHandler(queueHandler)

    logger.setLevel(logging.DEBUG)

    return logger

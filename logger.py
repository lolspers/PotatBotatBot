from __future__ import annotations

import contextlib
import logging
import sys
from datetime import datetime
from typing import TYPE_CHECKING

import colorama
from colorama import Fore, Style
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


class StreamFormatter(logging.Formatter):
    def __init__(self, config: Config):
        self.config: Config = config

        super().__init__("%(message)s")


    def format(self, record: logging.LogRecord) -> str:
        if self.config:
            record.msg = str(record.msg)

            time = ""
            if self.config.printTime and (getattr(record, "time", None) is not False):
                time = datetime.now().strftime("[%H:%M:%S] ")

            if getattr(record, "escape", None):
                record.msg = ascii(demojize(record.msg))

            if self.config.printColor:
                time = Style.DIM + time + Style.NORMAL
                ansiColor = getattr(record, "color", None)
                if ansiColor is None:
                    ansiColor = logColors.get(record.levelno, Fore.WHITE)

                record.msg = f"{ansiColor}{record.msg}"

            record.msg = f"{time}{record.msg}"

            record.msg = emojize(record.msg) if self.config.printEmojis else demojize(record.msg)

        return super().format(record)


class FileFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)

        data = getattr(record, "data", None)
        if isinstance(data, (dict, list)):
            with contextlib.suppress(TypeError):
                formatted += f"Extra data:\n {data!s}"

        return formatted


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



def getLogger(config: Config) -> logging.Logger:
    logger = logging.getLogger(__name__)

    fileHandler = logging.FileHandler("logs.log", encoding="utf-8")
    fileHandler.addFilter(FileFilter())
    fileHandler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    fileHandler.setLevel(config.loggingLevel)

    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.addFilter(StreamLevelFilter(level=config.consoleLoggingLevel))
    streamHandler.setFormatter(StreamFormatter(config))
    streamHandler.setLevel(logging.DEBUG)

    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)

    logger.setLevel(logging.DEBUG)

    return logger

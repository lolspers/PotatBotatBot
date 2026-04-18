import logging

import config as configModule
from logger import getLogger

__all__ = [
    "config", "logger",
]

config: configModule.Config = configModule.Config()

logger: logging.Logger = getLogger(config)

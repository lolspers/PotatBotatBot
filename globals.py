import logging

import config as configModule
import logger as loggerModule

__all__ = [
    "config", "logger",
]

config: configModule.Config = configModule.Config()

logger: logging.Logger = loggerModule.getLogger(config)

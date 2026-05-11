import logging
import os

import pbb.config as configModule
import pbb.logger as loggerModule

__all__ = [
    "config", "logger", "packageDir",
]

packageDir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

config: configModule.Config = configModule.Config(packageDir)

logger: logging.Logger = loggerModule.getLogger(config)

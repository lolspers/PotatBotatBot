import logging

logger = logging.getLogger("logger")

fileHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
fileHandler.setFormatter(formatter)

logger.addHandler(fileHandler)
logger.setLevel(30)
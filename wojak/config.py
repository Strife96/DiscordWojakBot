import json
import logging

logger = logging.getLogger("config")
logger.info("Running config...")

def loadConfig():
    global cfg
    try:
        with open("config.json", "r") as f:
            try:
                cfg = json.load(f)
                logger.info("configuration loaded successfully!")
                return True
            except json.decoder.JSONDecodeError as e:
                logger.critical("config.json not formatted properly {0}".format(e))
                return False
    except FileNotFoundError as e:
        logger.critical("config.json file not found in root folder... {0}".format(e))
        return False

if not loadConfig():
    logger.critical("Initial bot configuration failed. Ensure config.json file is in root directory and is properly formatted.")


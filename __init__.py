import wojak
import logging
import os

LOGGER_NAMES = ["__init__", "botframe", "commands",
                "config", "database", "functions", "blackjack"]

if os.path.exists("WojaksBadDay"):
    mode = "a"
else:
    mode = "w"

# set up logging to file
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s : %(message)s',
                    filename='WojaksBadDay',
                    filemode=mode)

for name in LOGGER_NAMES:
    logger = logging.getLogger(name)
    if name == "__init__":
        logger.info("\n<----- Wojak is getting out of bed ----->\n")
    logger.info("Initializing module logger...")

wojak.botframe.bot.run(wojak.config.cfg['bot']['token'])

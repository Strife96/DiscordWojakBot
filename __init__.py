import logging
import os

LOGGER_NAMES = ["__init__", "botframe", "commands", "configuration"]

if os.path.exists("WojacksBadDay"):
    mode = "a"
else:
    mode = "w"

#set up logging to file
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s %(name)s : %(message)s', 
                    filename='WojacksBadDay',
                    filemode=mode)

for name in LOGGER_NAMES:
    logger = logging.getLogger(name)
    if name == "__init__":
        logger.info("\n<----- Wojack is getting out of bed ----->\n")
    logger.info("Initializing module logger...")

import wojack.configuration
import wojack.botframe
import wojack.commands

wojack.botframe.bot.run(wojack.configuration.config['bot']['token'])


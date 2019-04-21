import logging
import os



if os.path.exists("WojacksBadDay"):
    mode = "a"
else:
    mode = "w"

#set up logging to file
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s %(name)s : %(message)s', 
                    filename='WojacksBadDay',
                    filemode=mode)

logger = logging.getLogger(__name__)
logger.info("Initializing logger...")

import wojack.configuration
import wojack.botframe
import wojack.commands

wojack.botframe.bot.run(wojack.configuration.config['bot']['token'])


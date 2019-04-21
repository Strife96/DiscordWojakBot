import logging

logger = logging.getLogger(__name__)
logger.info("Initializing logger...")

import sys
from . import configuration
from . import botframe

from discord.ext import commands

@botframe.bot.command(aliases=configuration.config['bot']['commands']['quit'])
async def quit(ctx):
    logging.shutdown()
    sys.exit(0)

@botframe.bot.command(aliases=configuration.config['bot']['commands']['hello'])
async def hello(ctx):
    await ctx.send("Hello, fren!")

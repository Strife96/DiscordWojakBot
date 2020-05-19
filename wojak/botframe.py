import discord
from discord.ext import commands
from . import config
import logging

logger = logging.getLogger("botframe")
logger.info("Running botframe...")


bot = commands.Bot(
    command_prefix=config.cfg['bot']['prefix'],
    description=config.cfg['bot']['description']
)


@bot.event
async def on_ready():
    logger.info(
        f"Wojak is alive! Logged in to Discord as '{bot.user.name}' ({bot.user.id})"
    )
    await bot.change_presence(
        activity=discord.Game(name=config.cfg['bot']['playing'])
    )

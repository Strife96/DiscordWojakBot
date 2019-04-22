import logging

logger = logging.getLogger("botframe")
logger.info("Running botframe...")

from . import config

from discord.ext import commands
import discord

bot = commands.Bot(command_prefix=config.cfg['bot']['prefix'], description=config.cfg['bot']['description'])

@bot.event
async def on_ready():
    logger.info("Wojak is alive! Logged in to Discord as '{0.user.name}' ({0.user.id})".format(bot))
    
    await bot.change_presence(activity=discord.Game(name=config.cfg['bot']['playing']))

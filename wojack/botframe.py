import logging

logger = logging.getLogger("botframe")
logger.info("Running botframe...")

from . import configuration

from discord.ext import commands
import discord

bot = commands.Bot(command_prefix=configuration.config['bot']['prefix'], description=configuration.config['bot']['description'])

@bot.event
async def on_ready():
    logger.info("Wojack is alive! Logged in to Discord as '{0.user.name}' ({0.user.id})".format(bot))
    
    await bot.change_presence(activity=discord.Game(name=configuration.config['bot']['playing']))

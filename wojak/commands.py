import logging

logger = logging.getLogger("commands")
logger.info("Running commands...")

import sys
from . import config
from . import botframe
from . import functions
from . import database

from discord.ext import commands
from discord import embeds, file

@botframe.bot.command(aliases=config.cfg['bot']['commands']['hello'])
async def hello(ctx):
    await ctx.send("Hello, fren!")
    logger.info("Hello, fren!")

@botframe.bot.command(aliases=config.cfg['bot']['commands']['wojak'])
async def wojak(ctx):
    blob = database.chooseRandom(database.wojackdb, database.IDpool) 
    newFile = functions.blobToFile(blob)
    await ctx.send(file=newFile)

@botframe.bot.command(aliases=config.cfg['bot']['commands']['add'])
async def add(ctx):
    blob = functions.imgToBlob("testwojak.jpg")
    database.addToDB(blob)
    logger.info("adding to database...")


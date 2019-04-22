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
    logger.info("posting a random boi...")
    img = functions.chooseRandom(database.wojakdb, database.IDpool) 
    newFile = functions.blobToFile(img[0], img[1])
    await ctx.send(file=newFile)

@botframe.bot.command(aliases=config.cfg['bot']['commands']['add'])
async def add(ctx):
    blob = functions.imgToBlob("testwojak.jpg")
    database.IDpool = functions.addToDB(database.wojakdb, blob, database.IDpool)


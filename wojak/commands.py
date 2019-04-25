﻿import logging

logger = logging.getLogger("commands")
logger.info("Running commands...")

import sys
import os
from . import config
from . import botframe
from . import functions
from . import database

from discord.ext import commands
from discord import file
import discord.utils

@botframe.bot.command(aliases=config.cfg['bot']['commands']['hello'])
async def hello(ctx):
    msg = functions.chooseRandomGreeting(config.cfg['greetings'])
    await ctx.send(msg)

@botframe.bot.command(aliases=config.cfg['bot']['commands']['wojak'])
@commands.cooldown(1, 15, commands.BucketType.user)
async def wojak(ctx):
    logger.info("posting a random boi...")
    img = functions.chooseRandomImg(database.wojakdb, database.IDpool) 
    newFile = functions.blobToFile(img[0], img[1])
    await ctx.send(file=newFile)

@botframe.bot.command(aliases=config.cfg['bot']['commands']['_add'])
async def _add(ctx, msgID):
    if fromAdmin(ctx):
        try:
            msg = await ctx.fetch_message(id=msgID)
            if msg.attachments:
                attach = msg.attachments[0]
                ext = functions.getExtension(attach)
                if ext in config.cfg['db']['extensions']:
                    blob = await functions.fileToBlob(attach)
                    ext = functions.getExtension(attach)
                    if blob:
                        database.IDpool = functions.addToDB(database.wojakdb, blob, ext, database.IDpool)
                        await ctx.message.add_reaction("👍")
                    else:
                        logger.critical("blob error occurred...")
                        await ctx.message.add_reaction("👎")
                else:
                    logger.critical("extension not allowed...")
                    await ctx.message.add_reaction("👎")
            else:
                logger.critical("message had no attachments...")
                await ctx.message.add_reaction("👎")
        except Exception as e:
            logger.critical("error occurred adding image {0}. {1}".format(msgID, e))
            await ctx.message.add_reaction("👎")
            raise # discord should ignore this, but I still want to see error output
    else:
        await ctx.send("Permission denied...")


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_remove'])
async def _remove(ctx, imgName):
    try:
        if fromAdmin(ctx):
            database.IDpool = functions.removeFromDB(database.wojakdb, imgName, database.IDpool)
            await ctx.message.add_reaction("👍")
        else:
            await ctx.send("Permission denied...")
    except Exception as e:
        logger.critical("error occured while removing img {0}. {1}".format(imgName, e))
        await ctx.message.add_reaction("👎")
        raise


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_resetpool'])
async def _resetpool(ctx):
    try:
        database.IDpool = functions.resetPool(database.wojakdb)
        await ctx.send("Pool reset successful. Pool size is now {0}".format(len(database.IDpool)))
    except Exception as e:
        logger.critical("error occurred while resetting pool. {0}".format(e))
        await ctx.send("I don't feel so good...")
        raise


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_checkdb'])
async def _checkdb(ctx):
    try:
        size = os.stat(config.cfg['db']['path']).st_size
        count = len(functions.getAllID(database.wojakdb))
        poolsize = len(database.IDpool)
        await ctx.send("Database size is {0} bytes. Number of records is {1}. Pool size is {2}.".format(size, count, poolsize))
    except Exception as e:
        logger.critical("error occurred while checking db. {0}".format(e))
        await ctx.send("I don't feel so good...")
        raise


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_shutdown'])
async def _shutdown(ctx):
    if fromAdmin(ctx):
        await botframe.bot.close()
        sys.exit(0)
    else:
        await ctx.send("Permission denied...")

def fromAdmin(ctx):
    return (ctx.message.author.id == config.cfg['permissions']['admin'])



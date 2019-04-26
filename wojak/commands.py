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

HELP_STRING = "```" + config.cfg['bot']['description'] + \
'''\n
Prefix: ?
Commands:
    info / help - display basic info on bot and commands
    hello / hi / hey - say hi to Wojak and he'll say hi back 
    wojak - post a random picture of Wojak and frens
    new_fren - get a link to add Wojak to your server
\n```
'''
botframe.bot.remove_command('help')

@botframe.bot.command(aliases=config.cfg['bot']['commands']['info'])
async def info(ctx):
    await ctx.send(HELP_STRING)

@botframe.bot.command(aliases=config.cfg['bot']['commands']['hello'])
async def hello(ctx):
    msg = functions.chooseRandomGreeting(config.cfg['greetings'])
    await ctx.send(msg)

@botframe.bot.command(aliases=config.cfg['bot']['commands']['wojak'])
@commands.cooldown(1, 15, commands.BucketType.channel)
async def wojak(ctx):
    logger.info("posting a random boi...")
    img = functions.chooseRandomImg(database.wojakdb, database.IDpool) 
    newFile = functions.blobToFile(img[0], img[1])
    await ctx.send(file=newFile)


@botframe.bot.command(aliases=config.cfg['bot']['commands']['new_fren'])
async def new_fren(ctx):
    logger.info("posting inv link for user {0} from guild {1}".format(ctx.message.author, ctx.message.channel.guild))
    await ctx.send(config.cfg['bot']['invite'])

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
    else:
        await ctx.send("Permission denied...")


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_remove'])
async def _remove(ctx, imgName):
    if fromAdmin(ctx):
        database.IDpool = functions.removeFromDB(database.wojakdb, imgName, database.IDpool)
        await ctx.message.add_reaction("👍")
    else:
        await ctx.send("Permission denied...")


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_resetpool'])
async def _resetpool(ctx):
    if fromAdmin(ctx):
        database.IDpool = functions.resetPool(database.wojakdb)
        await ctx.send("Pool reset successful. Pool size is now {0}".format(len(database.IDpool)))
    else:
        await ctx.send("Permission denied...")


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_checkdb'])
async def _checkdb(ctx):
    if fromAdmin(ctx):
        size = os.stat(config.cfg['db']['path']).st_size
        count = len(functions.getAllID(database.wojakdb))
        poolsize = len(database.IDpool)
        await ctx.send("Database size is {0} bytes. Number of records is {1}. Pool size is {2}.".format(size, count, poolsize))
    else:
        await ctx.send("Permission denied...")
        

@botframe.bot.command(aliases=config.cfg['bot']['commands']['_shutdown'])
async def _shutdown(ctx):
    if fromAdmin(ctx):
        await botframe.bot.close()
        sys.exit(0)
    else:
        await ctx.send("Permission denied...")

def fromAdmin(ctx):
    return (ctx.message.author.id == config.cfg['permissions']['admin'])



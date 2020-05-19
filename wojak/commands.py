import discord.utils
from discord.ext import commands
from . import blackjack
from . import database
from . import functions
from . import botframe
from . import config
import asyncio
import os
import sys
import logging

logger = logging.getLogger("commands")
logger.info("Running commands...")


HELP_STRING = "```" + config.cfg['bot']['description'] + \
    f'''\n
Prefix: {config.cfg['bot']['prefix']}
Commands:
    info / help - display basic info on bot and commands
    hello / hi / hey - say hi to Wojak and he'll say hi back
    wojak - post a random picture of Wojak and frens
    woblakjak - play a game of blackjack vs wojak
    new_fren - get a link to add Wojak to your server
\n```
'''
botframe.bot.remove_command('help')

# print basic bot info


@botframe.bot.command(aliases=config.cfg['bot']['commands']['info'])
async def info(ctx):
    await ctx.send(HELP_STRING)

# say hi to wojak and he'll say hi back


@botframe.bot.command(aliases=config.cfg['bot']['commands']['hello'])
async def hello(ctx):
    msg = functions.chooseRandomGreeting(config.cfg['greetings'])
    await ctx.send(msg)

# retrieves an image from the database and
# posts it to channel where request occurred


@botframe.bot.command(aliases=config.cfg['bot']['commands']['wojak'])
@commands.cooldown(1, 15, commands.BucketType.channel)
async def wojak(ctx):
    logger.info("posting a random boi...")
    img = functions.chooseRandomImg(database.wojakdb, database.IDpool)
    newFile = functions.blobToFile(img[0], img[1])
    await ctx.send(file=newFile)

# posts a message containing the invite link
# for this bot to join other servers.


@botframe.bot.command(aliases=config.cfg['bot']['commands']['new_fren'])
async def new_fren(ctx):
    logger.info("posting inv link for user {0} from guild {1}".format(
        ctx.message.author, ctx.message.channel.guild))
    await ctx.send(config.cfg['bot']['invite'])

# begins a game of blackjack in the channel where this command was found.


@botframe.bot.command(aliases=config.cfg['bot']['commands']['woblackjack'])
@commands.cooldown(3, 30, commands.BucketType.channel)
async def woblackjack(ctx):
    if ctx.message.author.id in database.blackjackPlayers:
        await ctx.send("Sorry, you can only play in one game at a time.")
    elif ctx.channel.id not in database.blackjackChannels:
        database.blackjackChannels.add(ctx.channel.id)
        game = blackjack.Game(ctx,
                              database.moneydbpath,
                              database.blackjackChannels,
                              database.blackjackPlayers)
        database.awaitPool.append(asyncio.create_task(game.runGame()))
    else:
        await ctx.send("A game is already running in this channel")


# adds several images to the database using their msgIDs, separated by spaces.
@botframe.bot.command(aliases=config.cfg['bot']['commands']['_add'])
async def _add(ctx, *msgIDs):
    if fromAdmin(ctx):
        resultStr = ""
        addedStr = ""
        notAddedStr = ""
        for msgID in msgIDs:
            try:
                msg = await ctx.fetch_message(id=msgID)
                if msg.attachments:
                    attach = msg.attachments[0]
                    ext = functions.getExtension(attach)
                    if ext in config.cfg['db']['extensions']:
                        blob = await functions.fileToBlob(attach)
                        ext = functions.getExtension(attach)
                        if blob:
                            database.IDpool = functions.addToDB(
                                database.wojakdb, blob, ext, database.IDpool)
                            addedStr += f"{msgID}; "
                        else:
                            logger.critical("blob error occurred...")
                            notAddedStr += f"{msgID}, blob error; "
                    else:
                        logger.critical("extension not allowed...")
                        notAddedStr += f"{msgID}, incorrect extension; "
                else:
                    logger.critical("message had no attachments...")
                    notAddedStr += f"{msgID}, no attachments; "
            except discord.HTTPException as e:
                logger.critical(f"HTTP error occured: {e}")
                notAddedStr += f"{msgID}, bad http request; "
        resultStr = f"👍 Added: {addedStr} \n\n 👎 Failed: {notAddedStr}"
        await ctx.send(resultStr)
    else:
        await ctx.send("Permission denied...")

# removes an image from the database based on the image filename.


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_remove'])
async def _remove(ctx, imgName):
    if fromAdmin(ctx):
        database.IDpool = functions.removeFromDB(
            database.wojakdb, imgName, database.IDpool)
        await ctx.message.add_reaction("👍")
    else:
        await ctx.send("Permission denied...")

# reseets the image IDpool and outputs current pool size.


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_resetpool'])
async def _resetpool(ctx):
    if fromAdmin(ctx):
        database.IDpool = functions.resetPool(database.wojakdb)
        await ctx.send(
            f"Pool reset successful. Pool size is now {len(database.IDpool)}"
        )
    else:
        await ctx.send("Permission denied...")

# outputs size of database in bytes, number of records
# in database, and number of IDs in pool.
# the record count and pool size should always match.


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_checkdb'])
async def _checkdb(ctx):
    if fromAdmin(ctx):
        size = os.stat(config.cfg['db']['path']).st_size
        count = len(functions.getAllID(database.wojakdb))
        poolsize = len(database.IDpool)
        await ctx.send(
            f"Database size is {size} bytes. Number of "
            f"records is {count}. Pool size is {poolsize}."
        )
    else:
        await ctx.send("Permission denied...")

# closes the bot's connection to discord and exits program.


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_shutdown'])
async def _shutdown(ctx):
    if fromAdmin(ctx):
        for task in database.awaitPool:
            await task
        await botframe.bot.close()
        sys.exit(0)
    else:
        await ctx.send("Permission denied...")

# verifies whether or not a message came from the bot admin.


def fromAdmin(ctx):
    return (ctx.message.author.id == config.cfg['permissions']['admin'])

import discord.utils
from discord.ext import commands
from . import blackjack
from . import database
from . import functions
from . import botframe
from . import config
from . import s3images
import asyncio
import sys
import logging

logger = logging.getLogger("commands")
logger.info("Running commands...")

WOJAK_IMAGE_BUCKET = config.cfg['aws']['wojak_image_bucket']

EXTENSIONS = [
    ".jpg",
    ".gif",
    ".bmp",
    ".png",
    ".JPG",
    ".GIF",
    ".BMP",
    ".PNG"
]

HELP_STRING = "```" + config.cfg['bot']['description'] + \
    f'''\n
Prefix: {config.cfg['bot']['prefix']}
Commands:
    info / help - display basic info on bot and commands
    hello / hi / hey - say hi to Wojak and he'll say hi back
    wojak - post a random picture of Wojak and frens
    woblakjak - play a game of blackjack vs wojak
    newfren - get a link to add Wojak to your server
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


@botframe.bot.command()
@commands.cooldown(1, 15, commands.BucketType.channel)
async def wojak(ctx):
    logger.info("posting a random boi...")
    img = s3images.chooseRandomImg(WOJAK_IMAGE_BUCKET, database.IDpool)
    name = img[0] + img[2]  # img[0] is ID, img[2] is file extension from Metadata
    newFile = functions.blobToFile(name, img[1])
    await ctx.send(file=newFile)


@botframe.bot.command(aliases=config.cfg['bot']['commands']['newfren'])
async def newfren(ctx):
    """posts a message containing the invite link for this bot to join other servers."""

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
@botframe.bot.command()
async def _add(ctx, *msgIDs):
    """
        Adds an image to the wojak s3 bucket
    """
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
                    if ext in EXTENSIONS:
                        blob = await functions.fileToBlob(attach)
                        ext = functions.getExtension(attach)
                        if blob:
                            database.IDpool = s3images.addToS3(
                                WOJAK_IMAGE_BUCKET, blob, ext, database.IDpool)
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


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_remove'])
async def _remove(ctx, imgName):
    """
        Removes an image from wojak s3 bucket by ID
    """
    if fromAdmin(ctx):
        database.IDpool = s3images.removeFromS3(
            WOJAK_IMAGE_BUCKET, imgName, database.IDpool)
        await ctx.message.add_reaction("👍")
    else:
        await ctx.send("Permission denied...")


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_resetpool'])
async def _resetpool(ctx):
    """
        Resets the image pool to align with the number of images currently in the s3 bucket
    """
    if fromAdmin(ctx):
        database.IDpool = s3images.resetPool(WOJAK_IMAGE_BUCKET)
        await ctx.send(
            f"Pool reset successful. Pool size is now {len(database.IDpool)}"
        )
    else:
        await ctx.send("Permission denied...")


@botframe.bot.command(aliases=config.cfg['bot']['commands']['_checkdb'])
async def _checkdb(ctx):
    """
        Outputs the number of records in the s3 bucket as well as internal pool size
    """
    if fromAdmin(ctx):
        count = len(s3images.getAllID(WOJAK_IMAGE_BUCKET))
        poolsize = len(database.IDpool)
        await ctx.send(
            f"Number of records is {count}. Pool size is {poolsize}."
        )
    else:
        await ctx.send("Permission denied...")

# closes the bot's connection to discord and exits program.

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

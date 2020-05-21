import discord
from random import randrange
import sqlite3
import io
import logging

logger = logging.getLogger("functions")
logger.info("Starting functions...")


MAX_SQLINT = 9223372036854775807


def blobToFile(name, blob):
    newFile = None
    try:
        with io.BytesIO(blob) as fp:
            newFile = discord.File(fp, name)
    except FileNotFoundError as e:
        logger.critical(
            "filename used to initialize object not found. {0}".format(e)
        )
    except IOError as e:
        logger.critical(
            "an error occured while reading/writing files. {0}".format(e)
        )
    return newFile


async def fileToBlob(attach):
    buf = io.BytesIO()
    blob = None
    # a hacky check, but this attribute only exists for images
    if attach.height:
        try:
            await attach.save(buf)
            with buf:
                blob = buf.read()
        except Exception as e:
            # ensure that blob is always None
            # if error occurs, but relay error to log
            logger.critical("error occured while blobbing file. {0}".format(e))
            blob = None
    else:
        logger.critical("attachment was not an image...")
        blob = None
    return blob


def getExtension(attach):
    return ("." + attach.filename.split(".")[-1])


def addToPool(pool, ID):
    pool.append(ID)
    return pool


def removeFromPool(pool, ID):
    pool.remove(ID)
    return pool


def chooseRandom(pool):
    return randrange(0, len(pool))


def chooseRandomGreeting(pool):
    logger.info("choosing random greeting...")
    choice = chooseRandom(pool)
    return pool[choice]


def createConnection(path):
    return sqlite3.connect(path)

import logging

logger = logging.getLogger("functions")
logger.info("Starting functions...")

import io
import os
import sqlite3
from hashlib import sha256
from random import randrange
import discord

MAX_SQLINT = 9223372036854775807

def blobToFile(name, blob):
    newFile = None
    try:
        with io.BytesIO(blob) as fp:
            newFile = discord.File(fp, name)
    except FileNotFoundError as e:
        logger.critical("filename used to initialize object not found. {0}".format(e))
    except IOError as e:
        logger.critical("an error occured while reading/writing files. {0}".format(e))
    return newFile

async def fileToBlob(attach):
    buf = io.BytesIO()
    blob = None
    if attach.height: # a hacky check, but this attribute only exists for images
        try:
            await attach.save(buf)
            with buf as fp:
                blob = buf.read()
        except Exception as e: # ensure that blob is always None if error occurs, but relay error to log
            logger.critical("error occured while blobbing file. {0}".format(e))
            blob = None
    else:
        logger.critical("attachment was not an image...")
        blob = None
    return blob

def isDupe(db, newID):
    allID = getAllID(db)
    for oldID in allID:
        if newID == oldID[0]:
            return True
    return False

def getExtension(attach):
    return ("." + attach.filename.split(".")[-1])

def addToDB(db, blob, extension, pool):
    digest = sha256(blob).hexdigest()
    digestStr = str(digest)
    imgID = int(digestStr, 16) % MAX_SQLINT
    name = digestStr + extension
    logger.info("name is {0}...".format(name))
    if isDupe(db, imgID):
        logger.info("duplicate image not added, hash {0}".format(imgID))
        return pool
    else:
        db.execute("insert into wojaks values (?, ?, ?)", (imgID, name, blob))
        logger.info("logging new image with id {0} , and name {1}".format(imgID, name))
        return addToPool(pool, imgID)

def removeFromDB(db, name, pool):
    try:
        db.execute("select distinct id, name from wojaks where name = ?", (name,))
        toRemove = db.fetchone()
        imgID = toRemove[0]
        name = toRemove[1]
        db.execute("delete from wojaks where id = ? and name = ?", (imgID, name))
        logger.info("deleted img with id = {0} and name = {1}".format(imgID, name))
        return removeFromPool(pool, imgID)
    except Exception as e:
        logger.critical("error occured while deleting. {0}".format(e))
        raise

def getAllID(db):
    db.execute("select id from wojaks")
    allID = db.fetchall()
    return allID

def resetPool(db):
    logger.info("resetting ID pool...")
    pool = []
    allID = getAllID(db)
    for ID in allID:
        pool.append(ID[0])
    logger.info("Pool size is now {0}".format(len(pool)))
    return pool

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

def chooseRandomImg(db, pool):
    choice = chooseRandom(pool)
    ID = pool[choice]
    db.execute("select name, img from wojaks where id = ?", (ID,))
    img = db.fetchone()
    return img

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

def removeTemp():
    os.remove(TEMP)

def imgToBlob(filename):
    blob = None
    try:
        with open(filename, "rb") as fp:
            blob = fp.read()
    except FileNotFoundError as e:
        logger.critical("filename used to create blob not found. {0}".format(e))
    return blob

def isDupe(db, newID):
    allID = getAllID(db)
    for oldID in allID:
        if newID == oldID[0]:
            return True
    return False

def addToDB(db, blob, pool):
    digest = sha256(blob).hexdigest()
    digestStr = str(digest)
    imgID = int(digestStr, 16) % MAX_SQLINT
    name = digestStr + ".jpg"
    if isDupe(db, imgID):
        logger.info("duplicate image not added, hash {0}".format(imgID))
        return pool
    else:
        db.execute("insert into wojaks values (?, ?, ?)", (imgID, name, blob))
        logger.info("logging new image with id {0} , and name {1}".format(imgID, name))
        return resetPool(db)

def getAllID(db):
    db.execute("select id from wojaks")
    allID = db.fetchall()
    return allID

def resetPool(db):
    logger.info("resetting ID pool...")
    pool = []
    allID = getAllID(db)
    for ID in allID:
        logger.info("Adding {0} to pool".format(ID[0]))
        pool.append(ID[0])
    logger.info(str(pool))
    return pool

def chooseRandom(db, pool):
    logger.info("choosing random from pool {0}".format(pool))
    choice = randrange(0, len(pool))
    ID = pool[choice]
    db.execute("select name, img from wojaks where id = ?", (ID,))
    img = db.fetchone()
    return img

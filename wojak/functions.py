import logging

logger = logging.getLogger("functions")
logger.info("Starting functions...")

import io
import sqlite3
from hashlib import sha256
from discord import file

def blobToFile(blob):
    newFile = None
    try:
        with io.BytesIO(blob) as fp:
            newFile = discord.File(fp)
    except FileNotFoundError as e:
        logger.critical("filename used to initialize object not found. {0}".format(e))
    return newFile

def imgToBlob(filename):
    blob = None
    try:
        with open(filename, "rb") as fp:
            blob = read(discord.File(fp))
    except FileNotFoundError as e:
        logger.critical("filename used to create blob not found. {0}".format(e))
    return blob

def isDupe(db, newID):
    allID = getAllID(db)
    for oldID in allID:
        if newID == oldID[0]:
            return True
    return False

def addToDB(db, blob):
    imgID = int(sha256(blob))
    if isDupe(imgID):
        logger.info("duplicate image not added, hash {0}".format(imgID))
    else:
        db.execute("insert into wojaks values (?, ?)", (imgID, blob))

def getAllID(db):
    db.execute("select id from wojaks")
    allID = db.fetchall()
    return allID

def resetPool(db):
    pool = []
    allID = getAllID(db)
    for ID in allID:
        pool.append(ID[0])
    return pool

def chooseRandom(db, pool):
    choice = randrange(0, len(pool)-1)
    ID = pool[choice]
    db.execute("select img from wojaks where id = ?", (ID,))
    img = db.fetchone()[0]
    return img

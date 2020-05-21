from . import s3images
from . import config
import os
import sqlite3
import logging

logger = logging.getLogger("database")
logger.info("Starting database...")

dbpath = config.cfg['db']['path']
moneydbpath = config.cfg['moneydb']['path']

logger.info("Connecting to wojack image db...")
IDpool = s3images.resetPool(config.cfg['aws']['wojak_image_bucket'])
blackjackChannels = set()
blackjackPlayers = set()
awaitPool = []

# if db does not exist yet, create it, set cursor, and populate with schema
if not os.path.isfile(moneydbpath):
    logger.info("Initializing wojak money db...")
    moneyConn = sqlite3.connect(moneydbpath)
    moneyConn.isolation_level = None
    wojakMoneydb = moneyConn.cursor()
    wojakMoneydb.execute(
        "create table money (id integer primary key, wallet integer)")
    # only threads will interact with db after creation, this connection
    # can be closed now
    moneyConn.close()

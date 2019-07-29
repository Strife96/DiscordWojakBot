import logging

logger = logging.getLogger("database")
logger.info("Starting database...")

import sqlite3
import os
from . import config
from . import functions

dbpath = config.cfg['db']['path']
moneydbpath = config.cfg['moneydb']['path']

# if db does not exist yet, create it, set cursor, and populate with schema
if not os.path.isfile(dbpath):
    logger.info("Initializing wojack image db...")
    conn = sqlite3.connect(dbpath)
    conn.isolation_level = None
    wojakdb = conn.cursor()
    wojakdb.execute("create table wojaks (id integer primary key, name text, img blob)")
    IDpool = []
    blackjackChannels = set()
    blackjackPlayers = set()
    awaitPool = []
else:
    logger.info("Connecting to wojack image db...")
    conn = sqlite3.connect(dbpath)
    conn.isolation_level = None
    wojakdb = conn.cursor()
    IDpool = functions.resetPool(wojakdb)
    blackjackChannels = set()
    blackjackPlayers = set()
    awaitPool = []

if not os.path.isfile(moneydbpath):
    logger.info("Initializing wojak money db...")
    moneyConn = sqlite3.connect(moneydbpath)
    moneyConn.isolation_level = None
    wojakMoneydb = moneyConn.cursor()
    wojakMoneydb.execute("create table money (id integer primary key, wallet integer)")
    moneyConn.close() # only threads will interact with db after creation, this connection can be closed now

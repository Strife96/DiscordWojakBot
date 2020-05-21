from hashlib import sha256
from .functions import chooseRandom
from . import config
from boto3 import client
import logging


logger = logging.getLogger("s3images")
logger.info("Starting s3images...")
REGION_NAME = config.cfg['aws']['region']

# initialize s3 client
s3client = client('s3', region_name=REGION_NAME)


def getAllID(bucket: str) -> list:
    # get all objects from s3 bucket as list
    logger.info("Getting all IDs from S3... ")
    response = s3client.list_objects_v2(Bucket=bucket)
    logger.info(f"Response is: \n{response}")
    allID = []
    # if response not empty, add all key IDs to return list
    if response["KeyCount"] > 0:
        allObjects = response['Contents']
        for obj in allObjects:
            allID.append(obj['Key'])
    return allID


def resetPool(bucket: str) -> list:
    logger.info("resetting ID pool...")
    pool = []
    allID = getAllID(bucket)
    for ID in allID:
        pool.append(str(ID))
    logger.info("Pool size is now {0}".format(len(pool)))
    return pool


def addToPool(pool: list, ID: str) -> list:
    pool.append(str(ID))
    return pool


def removeFromPool(pool: list, ID: str) -> list:
    pool.remove(str(ID))
    return pool


def isDupe(bucket: str, newID: str) -> bool:
    allID = getAllID(bucket)
    for oldID in allID:
        if newID == oldID:
            return True
    return False


def addToS3(bucket: str, blob: bytes, extension: str, pool: list) -> list:
    digest = sha256(blob).hexdigest()
    digestStr = str(digest)[:16]  # trim string to 16 characters
    logger.info(f"ID is {digestStr}...")
    if isDupe(bucket, digestStr):
        logger.info(f"duplicate S3 image not added, hash {digestStr}")
        return pool
    else:
        s3client.put_object(Bucket=bucket, Key=digestStr, Body=blob, Metadata={"ext": extension})
        logger.info(f"logging new S3 image with id {digestStr}")
        return addToPool(pool, digestStr)


def removeFromS3(bucket: str, imgID: str, pool: list) -> list:
    try:
        s3client.delete_object(Bucket=bucket, Key=imgID)
        logger.info(f"deleted img with id = {imgID}")
        return removeFromPool(pool, imgID)
    except Exception as e:
        logger.critical("error occured while deleting. {0}".format(e))
        raise


def chooseRandomImg(bucket: str, pool: list) -> (str, bytes, str):
    choice = chooseRandom(pool)
    imgID = pool[choice]
    response = s3client.get_object(Bucket=bucket, Key=imgID)
    blob = response['Body'].read()
    img = (imgID, blob, response['Metadata']['ext'])
    return img

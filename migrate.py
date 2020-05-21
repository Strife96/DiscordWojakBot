from boto3 import client
import sqlite3

BUCKET_NAME = "wojaks-picture-book"

s3client = client('s3', region_name='us-west-1')

conn = sqlite3.connect("./WojaksPictureBook")
conn.isolation_level = None
wojakdb = conn.cursor()
wojakdb.execute("select * from wojaks")
result = wojakdb.fetchall()
for row in result:
    splitup = row[1].split(".")
    digest = splitup[0]
    extension = "." + splitup[1]
    digestStr = str(digest)[:16]  # trim string to 16 characters
    print(f"ID is {digestStr}...")
    s3client.put_object(Bucket=BUCKET_NAME, Key=digestStr, Body=row[2], Metadata={"ext": extension})
    print(f"logging new S3 image with id {digestStr}")

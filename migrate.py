import boto3
import sqlite3

conn = sqlite3.connect("./WojaksPictureBook")
conn.isolation_level = None
wojakdb = conn.cursor()
wojakdb.execute("select id from wojaks")
result = wojakdb.fetchall()
print(f"Result: \n{result}")

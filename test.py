from flask import Flask, render_template, jsonify, redirect, request, url_for, flash
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy
import time
import random



# Connecting to our MySql Database
# https://pypi.org/project/cloud-sql-python-connector/ 

connector = Connector()

def getconn() -> pymysql.connections.Connection:
    conn: pymysql.connections.Connection = connector.connect(
        "cs411-juicyfruit:us-central1:cs411-juicyfruit",
        "pymysql",
        user="root",
        password="juicyfruit1234",
        db="juicyfruit_db",
    )
    return conn

pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

connection = pool.raw_connection()

id = "Afifs0918"
password = "juicyfruit1234"
name = "Afif"
computerid = random.randint(1000, 5000)
#inputstr = f"'{id}', {computerid}, '{name}', '{password}'"
#print(inputstr)

cursor = connection.cursor()
cursor.callproc("user_data", [f"{id}", computerid, f"{name}", f"{password}"])
connection.commit()




#results = list(cursor.fetchall())
#print(results)
#cursor.close()

# Temp example to query database
#with pool.connect() as db_conn:
#    results = db_conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM User_Information")).fetchall()

#ret_list = []

#for row in results:
    #ret_list.append(row[0])

#print(type(results[0][0]))
#connector.close()

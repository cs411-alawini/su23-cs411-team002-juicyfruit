from flask import Flask, render_template, jsonify
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy

app = Flask(__name__)

connector = Connector()

# function to return the database connection
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


with pool.connect() as db_conn:
    results = db_conn.execute(sqlalchemy.text("SELECT Name FROM User_Information LIMIT 9")).fetchall()


for row in results:
    print(row)

connector.close()





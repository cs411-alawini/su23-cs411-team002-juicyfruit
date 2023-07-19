from flask import Flask, render_template, jsonify
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy

app = Flask(__name__)

# Connecting to our MySql Database
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

#Flask App Routes
@app.route('/')
def test():

    with pool.connect() as db_conn:
        results = db_conn.execute(sqlalchemy.text("SELECT Name FROM User_Information LIMIT 9")).fetchall()

    ret_list = []

    for row in results:
        ret_list.append(row[0])

    print(ret_list)
    connector.close()

    return jsonify(ret_list)





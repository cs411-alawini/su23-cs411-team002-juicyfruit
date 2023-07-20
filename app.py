from flask import Flask, render_template, jsonify, redirect, request, url_for
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy

app = Flask(__name__)

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

#Flask App Routes
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        # verify username & password match in Database

        #eventually add way to make this redirect specific to the username & password, can str concatenate
        # username & password
        return redirect(url_for('gamesearch'))
    
    return render_template("login.html")
   
@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        #verify username is unique and add user to the database

        return redirect(url_for('gamesearch'))
    return render_template("signup.html")

#Eventually add customized gamesearch page based on individual users
@app.route('/gamesearch', methods=["GET", "POST"])
def gamesearch():
    if request.method == "POST":
        #Get the information for when the user clicks submit 
        category = request.form["category"]
        genre = request.form["genre"]
        price = request.form["price"]
        print(category)
        print(genre)
        print(price)
        

    return render_template("main.html")



# Temp example to query database
# with pool.connect() as db_conn:
#     results = db_conn.execute(sqlalchemy.text("SELECT Name FROM User_Information LIMIT 9")).fetchall()

# ret_list = []

# for row in results:
#     ret_list.append(row[0])

# print(ret_list)
# connector.close()

# return jsonify(ret_list)
from flask import Flask, render_template, jsonify, redirect, request, url_for, flash
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy
import random

app = Flask(__name__)
app.secret_key = 'juicyfruit1234234'

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
        #Verify username & password match in Database
        username = request.form["username"]
        password = request.form["password"]
        

        #Query to find if username & password combo exist
        with pool.connect() as db_conn:
            results = db_conn.execute(sqlalchemy.text(f"SELECT UserID, Password FROM User_Information WHERE UserID='{username}' AND Password='{password}'")).fetchall()

        #Redirect back to login if no user found
        if len(results) == 0:
            flash("Incorrect Username or Password, Please try again", 'error')
            return redirect(url_for('index'))
        
        #Eventually add way to make this redirect specific to the username & password, can str concatenate
        #username & password to the url
        return redirect(url_for('gamesearch'))
    
    return render_template("login.html")
   

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        # Verify username is unique and add user to the database
        # https://justinmatters.co.uk/wp/using-sqlalchemy-to-run-sql-procedures/ 
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        computerid = random.randint(1000,5000)

        #Adding user by calling stored procedure
        try:
           connection = pool.raw_connection() 
           cursor = connection.cursor()
           cursor.callproc("user_data", [f"{username}", computerid, f"{name}", f"{password}"])
           connection.commit()
        except:
            flash(f"{username} already has an account, login or create a unique username", 'error')
            return redirect(url_for('signup'))
        
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
        
        #TODO

    return render_template("main.html")

@app.route('/accountinfo', methods=["GET", "POST"])
def accountinfo():
    if request.method == "POST":
        #Verify information
        username = request.form["username"]
        old_password = request.form["password"]
        new_password = request.form["new_password"]

        #Update passoword
        try:
            connection = pool.raw_connection() 
            cursor = connection.cursor()
            cursor.callproc("update_password", [f"{username}", f"{old_password}", f"{new_password}"])
            connection.commit()
            flash("Password Updated Succesfully", 'message')
            return redirect(url_for('accountinfo'))
        except:
            flash("User not in database or wrong password", 'error')
            return redirect(url_for("accountinfo"))


    return render_template('accountinfo.html')

@app.route('/deleteaccount', methods=["GET", "POST"])
def deleteacc():
    if request.method == "POST":
        username = request.form["username"]

        # Delete user
        try:
            connection = pool.raw_connection() 
            cursor = connection.cursor()
            cursor.callproc("delete_user", [f"{username}"])
            connection.commit()
            flash("User succesfully deleted from Database", 'message')
            return redirect(url_for("index"))
        except:
            flash("User not in Database", 'error')
            return redirect(url_for("deleteacc"))

    return render_template("deleteacc.html")


# GetGamesWithPrice    
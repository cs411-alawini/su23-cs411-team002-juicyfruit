from flask import Flask, render_template, jsonify, redirect, request, url_for, flash, session
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy
import random
import pandas as pd

app = Flask(__name__)
app.secret_key = 'juicyfruit1234'

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
# Login/Logout & Signup
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        
        #Verify username & password match in Database
        with pool.connect() as db_conn:
            results = db_conn.execute(sqlalchemy.text(f"SELECT UserID, Password FROM User_Information WHERE UserID='{username}' AND Password='{password}'")).fetchall()

        #Redirect back to login if no user found
        if len(results) == 0:
            flash("Incorrect Username or Password, please try again or signup for an account", 'error')
            return redirect(url_for('index'))

        #Using sessions so that user can later have personalized page
        session['username'] = username

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

        # Adding user by calling stored procedure
        try:
           connection = pool.raw_connection() 
           cursor = connection.cursor()
           cursor.callproc("user_data", [f"{username}", computerid, f"{name}", f"{password}"])
           connection.commit()
        except:
            flash(f"{username} already has an account, login or create a unique username", 'error')
            return redirect(url_for('signup'))
        
        #Adding username to session
        session['username'] = username

        return redirect(url_for('gamesearch'))
    
    return render_template("signup.html")

@app.route('/logout')
def logout():
    #Removes username from session when clicking logout button
    session.pop('username', None)
    flash('Successfully logged out', 'message')
    return redirect(url_for('index'))

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# User Account Routes
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

        #Ensure user doesn't delete others account
        if username != session['username']:
            flash("This username isn't for your account!", 'error')
            return redirect(url_for("deleteacc"))
        
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

@app.route('/addcomp', methods=["GET", "POST"])
def addcomp():
    if 'username' not in session:
        return redirect(url_for("index"))
    
    connection = pool.raw_connection() 
    cursor = connection.cursor()
    username = session['username']

    if request.method == "POST":
        os = request.form["operating_system"]
        cursor.callproc("add_comp", [username, os])
        connection.commit()
        flash("Added your computer info to account", "message")
        return redirect(url_for('accountinfo'))
    
    return render_template("addcomp.html")

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# User Friends Routes
@app.route('/friends', methods=["GET", "POST"])
def friends():
    #Check that the user is logged in
    if 'username' not in session:
        return redirect(url_for("index"))

    #Setting up connection & getting username
    connection = pool.raw_connection() 
    cursor = connection.cursor()
    username = session['username']

    #If we are just loading the friends list without adding a friend
    if request.method == "GET":

        cursor.execute(f"SELECT FriendID FROM Friends WHERE UserID='{username}'")
        friends = list(cursor.fetchall())
        connection.commit()


        return render_template("friends.html", friend_list=friends)

    # If user is adding to friends list
    friendusername = request.form['friendusername']

    #Make sure you aren't adding yourself
    if username == friendusername:
        flash("You can't add yourself as a friend!", "error")
        return redirect(url_for("friends", method="GET"))
    
    #See if we can add the friend to the list
    try:
        cursor.callproc("add_friend", [username, friendusername])
        connection.commit()
    except:
        flash("Friend you are trying to add is not in the database", "error")
        return redirect(url_for("friends", method="GET"))

    return redirect(url_for("friends", method="GET"))

@app.route('/removefriend', methods=["POST"])
def removefriend():
    #Check that the user is logged in
    if 'username' not in session:
        return redirect(url_for("index"))

    #Setting up connection & getting username
    connection = pool.raw_connection() 
    cursor = connection.cursor()
    username = session['username']
    frienduser = request.form["friendID"]

    #Deleting friend from list
    cursor.execute(f"DELETE FROM Friends WHERE UserID='{username}' AND FriendID='{frienduser}'")
    # TODO: Making sure to remove friends both ways?
    connection.commit()

    flash(f"Succesfully removed {frienduser} from your friends list", 'message')
    return redirect(url_for('friends'))

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Game Adding & Reccomendation Routes

@app.route('/games', methods=["GET", "POST"])
def games():
    if 'username' not in session:
        return redirect(url_for("index"))

    #Setting up connection & getting username
    connection = pool.raw_connection() 
    cursor = connection.cursor()
    username = session['username']

    #If just getting games list
    if request.method == "GET":

        cursor.execute(f"""SELECT GameName
                          FROM Games_Owned NATURAL JOIN
                          (SELECT GameID, GameName FROM Games) g
                           WHERE UserID='{username}'""")
        games = list(cursor.fetchall())
        connection.commit()


        return render_template("games.html", games_list=games)
    
    #If adding reccomendation
    if request.method == "POST":
        game_name = request.form["game_name"]
        rating = request.form["rating"]
        time_played = request.form["time_played"]

        cursor.execute(f"""SELECT GameID
                        FROM Games
                        WHERE GameName='{game_name}' """)

        try:
            gameid = list(cursor.fetchall())[0][0]
        except:
            flash("This game isn't in the database!", "error")
            return redirect(url_for("games"))

        try:
            reccid = random.randint(0,10000)
            cursor.callproc("user_review", 
                            [reccid, int(gameid), username, int(rating), int(time_played)])
            connection.commit()
        except:
            flash("Error adding reccomendation, check that the game is on your games list", 'error')
            return redirect(url_for("games"))
    
    flash("Game reccomendation successfully added", 'message')
    return redirect(url_for("games"))

@app.route('/removegame', methods=["POST"])
def removegame():
    if 'username' not in session:
        return redirect(url_for("index"))

    # Setting up connection & getting username
    connection = pool.raw_connection() 
    cursor = connection.cursor()
    username = session['username']
    game_name = request.form["game_name"]

    # Get GameID to remove
    cursor.execute(f"""SELECT GameID
                        FROM Games
                        WHERE GameName='{game_name}' """)
    
    # Remove Game
    gameid = list(cursor.fetchall())[0][0]
    cursor.execute(f"DELETE FROM Games_Owned WHERE UserID='{username}' AND GameID='{gameid}'")
    connection.commit()

    return redirect(url_for('games'))


@app.route('/searchgames', methods=["GET"])
def searchgames():
    keyword = request.args.get("keyword", '').strip()

    connection = pool.raw_connection() 
    cursor = connection.cursor()
    
    cursor.execute(f"""SELECT GameName
                        FROM Games 
                        WHERE GameName LIKE'%{keyword.lower()}%'""")
    data = list(cursor.fetchall())
    
    return jsonify(data)

@app.route('/addgame', methods=["GET"])
def addgame():
    if 'username' not in session:
        return redirect(url_for("index"))
    
    game_name = request.args.get("game_name", '').strip()
    username = session['username']
    connection = pool.raw_connection() 
    cursor = connection.cursor()

    cursor.execute(f"""SELECT GameID
                        FROM Games
                        WHERE GameName='{game_name}' """)
    try:
        gameid = list(cursor.fetchall())[0][0]
    except:
        flash("Error adding this game, try a different one", 'error')
        redirect(url_for("games"))

    #Check if game already already on the list
    cursor.execute(f"""SELECT GameID
                        FROM Games_Owned
                        WHERE UserID='{username}'""")
    gametpl=(gameid,)

    if gametpl not in list(cursor.fetchall()):
        cursor.callproc("add_owned_game", [username, int(gameid)])
        connection.commit()
        return redirect(url_for("games"))
    else:
        flash("Game already on your list!", "message")
        return redirect(url_for("games"))
    
@app.route('/friendgames', methods=["GET"])
def friendgames():
    connection = pool.raw_connection() 
    cursor = connection.cursor()
    frienduser = request.args.get("friendusername")

    cursor.execute(f"""SELECT GameName
                          FROM Games_Owned NATURAL JOIN
                          (SELECT GameID, GameName FROM Games) g
                           WHERE UserID='{frienduser}'""")
    games_list = list(cursor.fetchall())

    cursor.execute(f"""SELECT GameName, UserRating
                        FROM User_Recommended_Games
                        WHERE UserID='{frienduser}'""")
    
    rec_list = list(cursor.fetchall())

    connection.commit()

    return render_template("friendgames.html", 
                           friend=frienduser, 
                           games_list=games_list, 
                           rec_list=rec_list)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# GameSearch Routes
@app.route('/gamesearch', methods=["GET", "POST"])
def gamesearch():
    if request.method == "POST":
        #Get the information for when the user clicks submit 
        keyword = request.form["keyword"]
        category = request.form["category"]
        genre = request.form["genre"]
        price = request.form["price"]
        reviewscore = request.form["reviewscore"]
        
        connection = pool.raw_connection() 
        cursor = connection.cursor()

        if price != '' and reviewscore != '':
            # UnionQuery
            tpl = ("Game Name" , "Price", "Average Review Score", "Single Player?", "Multiplayer?")
            cursor.callproc("Unionquery", [float(price), float(reviewscore)/100])
        
        elif reviewscore != '':
            # RevScoreQuery
            tpl = ("Game Name", "Metacritic Rating", "Average Review Score")
            cursor.callproc("RevScoreQuery", [float(reviewscore)/100])

        elif price != '':
            # GetGamesWithPrice
            tpl = ("Game Name", "Release Date", "Price")
            cursor.callproc("GetGamesWithPrice", [float(price)])
            
        elif keyword != '':
            # Keyword Search
            tpl = ("Game Name", "Price", "Metacritic Rating")
            cursor.execute(f"SELECT GameName, Price, MetacriticRating FROM Games WHERE GameName LIKE '%{keyword.lower()}%'")

        data = list(cursor.fetchall())
        connection.commit()

        df = pd.DataFrame(data, columns=tpl)

        # Additional processing step for Unionquery
        if price != '' and reviewscore != '':
            df["Single Player?"] = df["Single Player?"].replace({1: 'Yes', 0: 'No'})
            df["Multiplayer?"] = df["Multiplayer?"].replace({1: 'Yes', 0: 'No'})

        table = df.to_html(classes='results-table', index=False)
        
        return render_template("displayquery.html", html_table=table)


    return render_template("main.html")



import os
import datetime

from flask import Flask, flash, redirect, render_template, request, session
from dotenv import load_dotenv
import psycopg2
from psycopg2 import extras
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from hash_maker import passwordfunc

# Configure application
app = Flask(__name__)

# Getting the URL for the cloud database
load_dotenv()
url = os.getenv("DATABASE_URL")

# Connecting to the PostgreSQL DB
conn = psycopg2.connect(url)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

invalid_chars = ["'", ";"]

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/home")
@login_required
def index():
    """Show table of passwords"""
    passwords = []
    with conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            username_query = cursor.mogrify("SELECT users.username FROM users WHERE users.id = %s", (session["user_id"],))
            cursor.execute(username_query)
            username = cursor.fetchone()
            passwords_query = cursor.mogrify("SELECT websites.name, websites.URL, user_passwords.username, user_passwords.email, user_passwords.password FROM user_passwords JOIN users ON users.id = user_passwords.user_id JOIN websites ON user_passwords.website_id = websites.id WHERE users.id = %s", (session["user_id"],))
            cursor.execute(passwords_query)
            passwords = cursor.fetchall()
    return render_template("index.html", username=username["username"], passwords=passwords)

@app.route("/")
def home():
    return render_template("homepage.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide a username", 400)
        elif not request.form.get("password"):
            return apology("Must provide a password", 400);

        # Query database for a username
        with conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                query = cursor.mogrify("SELECT * FROM users WHERE username = %s", (request.form.get("username"),))
                print(query)
                cursor.execute(query)
                rows = cursor.fetchall()
                print(rows)
                if rows:
                    if len(rows) != 1 or not check_password_hash((rows[0]['hash']), request.form.get("password")):
                        return apology("Invalid Username and/or Password", 400)
                
                    session["user_id"] = rows[0]["id"]

                    return redirect("/home")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or username == '':
            return apology("Must provide a username", 400)
        for char in username:
            if char in invalid_chars:
                return apology("Username has not appropiate characters", 400)
        if not password or password == '':
            return apology("Password not available", 400)
        if not confirmation or confirmation == '':
            return apology("Confirmation not available", 400)
        if password != confirmation:
            return apology("Passwords doesn't match", 400)
        
        for character in password:
            if character in invalid_chars:
                return apology("Password has not appropiate characters", 400)
        
        with conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute("SELECT username FROM users;")
                usernames = cursor.fetchall()
                if usernames:
                    for dict in usernames:
                        if username == dict['username']:
                            return apology("Username already exists", 400)
            
        has_symbol = False
        has_lower = False
        has_upper = False
        has_number = False
        requirements_meeted = False
        
        for char in password:
            if not char.isalnum() and not char.isspace():
                has_symbol = True
            if char.islower():
                has_lower = True
            if char.isupper():
                has_upper = True
            if char.isdigit():
                has_number = True
            
        if has_symbol and has_lower and has_upper and has_number:
            requirements_meeted = True
            
        if requirements_meeted == True:
            with conn:
                with conn.cursor() as cursor:
                    query = cursor.mogrify("INSERT INTO users (username, hash) VALUES (%s, %s);", (username, generate_password_hash(confirmation)))
                    cursor.execute(query)
            return redirect("/login")
        else:
            return apology("Password don't meet the requirements. Passwords must have symbols, digits, lower and upper case letters", 400)
            
    else: 
        return render_template("register.html")

@app.route("/logout")
def logout():
    """log User Out"""
    # Forget any user_id

    session.clear()

    # Redirect user to homepage
    return redirect("/home")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":

        app_name = request.form.get("name").capitalize()
        url = request.form.get("url")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not app_name or app_name == '':
            return apology("Invalid App name to store!", 400)
        elif not url or url == '':
            return apology("Invalid URL to store!", 400)
        elif not username or username == '':
            return apology("Invalid username to store!", 400)
        elif not email or email == '':
            return apology("Invalid email to store!", 400)
        elif not password or password == '':
            return apology("Invalid Password!", 400)
        
        with conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                current_apps_query = cursor.mogrify("SELECT websites.name FROM websites, user_passwords, users WHERE websites.id = user_passwords.website_id AND user_passwords.user_id = users.id AND users.id = %s;", (session["user_id"],))
                cursor.execute(current_apps_query)
                current_apps = cursor.fetchall()
                print(f"Current apps: {current_apps}")

                for row in current_apps:
                    if row['name'] == app_name:
                        return apology("This app name already exits in your vault, if you want to change something delete it and add another one!", 400)
                
                website_exits_in_table = False
                websites_data_query = cursor.mogrify("SELECT name FROM websites;")
                cursor.execute(websites_data_query)
                websites_data = cursor.fetchall()

                for website in websites_data:
                    if website['name'] == app_name:
                        website_exits_in_table = True
                        break
                
                print(f"El nombre de la pagina existe en la tabla?: {website_exits_in_table}")

                if website_exits_in_table == False:
                    query = cursor.mogrify("INSERT INTO websites (name, url) VALUES (%s, %s);", (app_name, url))
                    cursor.execute(query)

                app_id_query = cursor.mogrify("SELECT websites.id FROM websites WHERE websites.name = %s;", (app_name,))
                cursor.execute(app_id_query)
                app_id = cursor.fetchone()
                print(f"Id de la app: {app_id}")
                psw = passwordfunc(password, app_name, 12)
                query_to_execute = cursor.mogrify("INSERT INTO user_passwords (user_id, website_id, username, email, password) VALUES (%s, %s, %s, %s, %s) ", (session["user_id"], app_id['id'], username, email, psw))
                cursor.execute(query_to_execute)

        return redirect("/home")
    else:
        return render_template("add.html")

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():

    if request.method == "POST":

        name = request.form.get("name").capitalize()

        if not name or name == '':
            return apology("Name not send or invalid!")
        
        with conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                current_apps_query = cursor.mogrify("SELECT websites.name FROM websites, user_passwords, users WHERE websites.id = user_passwords.website_id AND user_passwords.user_id = users.id AND users.id = %s;", (session["user_id"],))
                cursor.execute(current_apps_query)
                current_apps = cursor.fetchall()

                current_app_exists_vault = False
                for app in current_apps:
                    if app['name'] == name:
                        current_app_exists_vault = True

                if current_app_exists_vault == False:
                    return apology("Application does not exist in yout vault!", 400)
                
                app_id_query = cursor.mogrify("SELECT websites.id FROM websites WHERE name = %s", (name,))
                cursor.execute(app_id_query)
                app_id = cursor.fetchone()
                delete_query = cursor.mogrify("DELETE FROM user_passwords WHERE website_id = %s AND user_id = %s", (app_id['id'], session["user_id"],))
                cursor.execute(delete_query)

        return redirect("/home")
    else:
        return render_template("delete.html")

@app.route("/quote", methods=["POST", "GET"])
@login_required
def quote():
    
    if request.method == 'POST':
        app_name = request.form.get("name").capitalize()

        if not app_name or app_name == '':
            return apology("App Name required or is invalid!", 400)

        with conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                passwords_query = cursor.mogrify("SELECT websites.name, websites.URL, user_passwords.username, user_passwords.email, user_passwords.password FROM user_passwords JOIN users ON users.id = user_passwords.user_id JOIN websites ON user_passwords.website_id = websites.id WHERE users.id = %s AND websites.name = %s", (session["user_id"], app_name))
                cursor.execute(passwords_query)
                passwords = cursor.fetchall()

        if not passwords:
            return apology("App not in vault!", 400)
        
        return render_template("quoted.html", passwords=passwords)

    else:
        return render_template("quote.html")

@app.route("/account")
@login_required
def account():
    with conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            username_query = cursor.mogrify("SELECT username FROM users WHERE id = %s", (session["user_id"],))
            cursor.execute(username_query)
            username = cursor.fetchone()
            number_apps_query = cursor.mogrify("SELECT COUNT(websites.name) AS number FROM websites, user_passwords, users WHERE websites.id = user_passwords.website_id AND user_passwords.user_id = users.id AND users.id = %s", (session["user_id"],))
            cursor.execute(number_apps_query)
            number_apps = cursor.fetchall()
            apps_query = cursor.mogrify("SELECT websites.name FROM websites, user_passwords, users WHERE websites.id = user_passwords.website_id AND user_passwords.user_id = users.id AND users.id = %s;", (session["user_id"],))
            cursor.execute(apps_query)
            apps = cursor.fetchall()

    return render_template("account.html", username=username, count_apps=number_apps[0], apps=apps)

if __name__ == "__main__":
    app.run(debug=True)
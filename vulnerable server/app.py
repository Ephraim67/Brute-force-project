# Importing
# import flask library
# Libraries: import Flask for web handling, flask_mysqldb for MySQL database connectivity, and re for input validation.
# step 1: install flask.
# to import the flasks scripts, 

from flask import Flask

# the line tells python to import the flask class from the library of the already installed framework (flask)
# this should server as the Web Server Gateway Interface

app = Flask(__name__)

# Project here is a variable that has been declared to define the site,
# Flask is the framework where the resource (_name_) is derived from. 


# setup flask app to access route path

@app.route('/')

# this line tells the framework what to do when someone visits "/" (the homepage).

def home():
    return 'Welcome to my page Mr Ephraim!'

if __name__ == '__main__':
    app.run(debug=True)

# it would be Running on http://127.0.0.1:5000 because it's built to run via that route on the framework (flask)

# Running the App: the app runs in debug mode, enabling easy debugging during development...
# Flask App Configuration: configures the app, including MySQL connection settings and a secret key for session handling.

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)
app.secret_key = '2238a7aba1fc8e32096d8cc9e93b0fad08ff23430aa03d5b97862492f649db1a'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'el'
app.config['MYSQL_PASSWORD'] = 'kali'   
app.config['MYSQL_DB']  = 'flaskapp'

mysql = MySQL(app)

# home route
@app.route('/')

# Login Route (/login): handles user authentication by checking the username and password against the database.

# login route
# define login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursor.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()

    if account:
        session['loggedin'] = True
        session['id'] = account['id']
        session['username'] = account['username']
        return redirect(url_for('home'))
    else:
        msg = 'Incorrect username/password!'

    return render_template('login.html', msg=msg)

# Logout Route (/logout): ends the session and redirects to the login page.

# logout route
# define logout route
@app.route('/logout')
def logout():
    session.pop('loggedin',None)
    session.pop('id',None)
    session.pop('username',None)

    return redirect(url_for('login'))

#Registration Route (/register): handles new user registrations by validating input and inserting user details into the database.

# register route
# define register route
@app.route('/register', methods=['GET', 'POST'])

def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = password.form['password']
        email= request.form['email']

        cursor = mysql.connection.cursor(MySQLdb.cursor.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username,))
        account = cursor.fetchone()
    if account:
        msg = 'Account already exists!'
    elif not username or not password or not email:
        msg = 'Please fill out the form!'
    else:
        cursor.execute('INSERT INTO account VALUES (NULL, %s, %s, %s)', (username, password, email))
        mysql.connection.commit()
        msg = 'You have successfully registered!'


    return render_template('register.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True)

#Running the App: the app runs in debug mode, enabling easy debugging during development.

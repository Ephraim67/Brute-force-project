from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['MYSQL_HOST'] = '_____________________'
app.config['MYSQL_USER'] = '___________'
app.config['MYSQL_PASSWORD'] = '_________'   
app.config['MYSQL_DB']  = '______________'

mysql = MySQL(app)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        




    return render_template('register.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True)
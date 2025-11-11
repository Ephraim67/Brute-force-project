import os
import re
from datetime import datetime, timedelta

import requests
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash

from flask_mysqldb import MySQL
import MySQLdb.cursors

from dotenv import load_dotenv
load_dotenv()

RATE_LIMIT = "5 per minute"        
LOCKOUT_THRESHOLD = 5              
LOCKOUT_MINUTES = 15               

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv('FLASK_SECRET', 'dev-fallback-secret-do-not-use-in-prod')

app.config.update(
    SESSION_COOKIE_SECURE=False,    
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=10)
)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'el')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'kali')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'flaskapp')

csrf = CSRFProtect(app)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

Talisman(app,
    content_security_policy={
        'default-src': ["'self'"],
        'script-src': ["'self'"],
        'style-src': ["'self'"],
    },
    force_https=False
)

mysql = MySQL(app)

def create_db_connection_cursor():
    """Return a cursor using DictCursor."""
    conn = mysql.connection
    return conn.cursor(MySQLdb.cursors.DictCursor)

@app.route('/')
def home():
    if 'loggedin' in session:
        return f"Welcome, {session['username']}!"
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit(RATE_LIMIT)
def login():
    msg = ''
    
    if 'loggedin' in session:
        session.clear()

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username'].strip()
        password = request.form['password']

        
        if len(username) > 150 or len(password) > 200:
            msg = "Invalid input."
            return render_template('login.html', msg=msg)

        cursor = create_db_connection_cursor()
        try:
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
        finally:
            cursor.close()

    
        if not account:
            app.logger.warning("Login attempt for non-existent username=%s from %s", username, request.remote_addr)
            msg = 'Incorrect username or password!'
            return render_template('login.html', msg=msg)

        
        lockout_until = account.get('lockout_until')
        if lockout_until:
            
            now = datetime.utcnow()
            if isinstance(lockout_until, datetime):
                expire_time = lockout_until
            else:
                
                try:
                    expire_time = datetime.strptime(lockout_until, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    expire_time = None
            if expire_time and now < expire_time:
                remaining = int((expire_time - now).total_seconds() // 60) + 1
                msg = f"Account locked. Try again in {remaining} minute(s)."
                return render_template('login.html', msg=msg)

        
        if check_password_hash(account['password'], password):
        
            cursor = create_db_connection_cursor()
            try:
                cursor.execute(
                    "UPDATE accounts SET failed_attempts = 0, lockout_until = NULL WHERE id = %s",
                    (account['id'],)
                )
                mysql.connection.commit()
            finally:
                cursor.close()

            
            session.clear()
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session.permanent = True
            return redirect(url_for('home'))

        
        failed_attempts = (account.get('failed_attempts') or 0) + 1
        lockout_ts = None

        if failed_attempts >= LOCKOUT_THRESHOLD:
            lockout_ts = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            msg = f"Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minute(s)."
        else:
            msg = f"Incorrect username or password! ({failed_attempts}/{LOCKOUT_THRESHOLD})"

        cursor = create_db_connection_cursor()
        try:
            cursor.execute(
                "UPDATE accounts SET failed_attempts = %s, lockout_until = %s WHERE id = %s",
                (failed_attempts, lockout_ts, account['id'])
            )
            mysql.connection.commit()
        finally:
            cursor.close()

        app.logger.warning("Failed login for username=%s (attempt %s) from %s",
                           username, failed_attempts, request.remote_addr)
        session.clear()  

    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("30 per minute")
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username'].strip()
        password = request.form['password']
        email = request.form['email'].strip()

        # server-side validation
        if not username or not password or not email:
            msg = 'Please fill out the form!'
            return render_template('register.html', msg=msg)

        if not re.match(r'^[A-Za-z0-9]+$', username) or len(username) > 150:
            msg = 'Username must contain only letters and numbers and be shorter than 150 chars!'
            return render_template('register.html', msg=msg)

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email) or len(email) > 255:
            msg = 'Invalid email address!'
            return render_template('register.html', msg=msg)

        cursor = create_db_connection_cursor()
        try:
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
                return render_template('register.html', msg=msg)

            hashed = generate_password_hash(password)

            cursor.execute(
                'INSERT INTO accounts (username, password, email, failed_attempts, lockout_until) VALUES (%s, %s, %s, %s, %s)',
                (username, hashed, email, 0, None)
            )
            mysql.connection.commit()
            app.logger.info("New user registered: %s", username)
            return redirect(url_for('login'))
        except Exception:
            app.logger.exception("Error registering user %s", username)
            msg = "An error occurred. Please try again later."
            return render_template('register.html', msg=msg)
        finally:
            cursor.close()

    return render_template('register.html', msg=msg)


@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('429.html', msg="Too many attempts. Try again later."), 429

@app.errorhandler(500)
def internal_error(e):
    app.logger.exception("Server error: %s", e)
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    
    app.run(debug=True, host='127.0.0.1', port=5000)

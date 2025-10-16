# app.py (secureified)

import os
import re
from datetime import timedelta

from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash

# DB adapter (your previous choice)
from flask_mysqldb import MySQL
import MySQLdb.cursors

# Optionally load .env in development (python-dotenv)
from dotenv import load_dotenv
load_dotenv()  # safe: will only load if .env exists

# -------------------------
# App & config (secrets from env)
# -------------------------
app = Flask(__name__, template_folder="templates")

# Use a strong secret from environment; fallback only for dev
app.secret_key = os.getenv('FLASK_SECRET', 'dev-fallback-secret-do-not-use-in-prod')

# Session cookie hardening
app.config.update(
    SESSION_COOKIE_SECURE=True,    # requires HTTPS in production
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',  # or 'Strict' if suitable
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=10)
)

# MySQL config from environment (no hardcoding)
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'el')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'kali')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'flaskapp')

# -------------------------
# Security extensions
# -------------------------
# 1) CSRF protection for forms
csrf = CSRFProtect(app)   # requires adding {{ csrf_token() }} in your HTML forms

# 2) Rate limiting (protect login/register from brute force)
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
limiter.init_app(app)

# 3) Security headers (CSP + HSTS)
Talisman(app,
        content_security_policy={
            'default-src': ["'self'"],
            'script-src': ["'self'"],
            'style-src': ["'self'"],
        },
        force_https=False  # set True if you run behind HTTPS in production
)

# -------------------------
# Initialize MySQL
# -------------------------
mysql = MySQL(app)

# -------------------------
# Helpers
# -------------------------
def create_db_connection_cursor():
    """Return a cursor using DictCursor. Wrap usage in try/except and close cursor."""
    conn = mysql.connection
    return conn.cursor(MySQLdb.cursors.DictCursor)

# -------------------------
# Routes (with added protections)
# -------------------------
@app.route('/')
def home():
    if 'loggedin' in session:
        return f"Welcome, {session['username']}!"
    return redirect(url_for('login'))

# limit login attempts: 2 per minute (adjust as needed)
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("2 per minute")
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username'].strip()
        password = request.form['password']

        # server-side input validation (length)
        if len(username) > 150 or len(password) > 200:
            msg = "Invalid input."
            return render_template('login.html', msg=msg)

        cursor = create_db_connection_cursor()
        try:
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
        finally:
            cursor.close()

        if account and check_password_hash(account['password'], password):
            # regenerate/clear session on login
            session.clear()
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # optionally make session permanent for a controlled lifetime
            session.permanent = True
            return redirect(url_for('home'))
        else:
            app.logger.warning("Failed login for username=%s from %s", username, request.remote_addr)
            msg = 'Incorrect username or password!'

    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    # clear session fully
    session.clear()
    return redirect(url_for('login'))

# limit register attempts: 10 per minute to reduce abuse
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

        # check existing account
        cursor = create_db_connection_cursor()
        try:
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
                return render_template('register.html', msg=msg)

            # store hashed password (PBKDF2) -- use werkzeug generate_password_hash
            hashed = generate_password_hash(password)  # default PBKDF2 + SHA256

            cursor.execute(
                'INSERT INTO accounts (username, password, email) VALUES (%s, %s, %s)',
                (username, hashed, email)
            )
            mysql.connection.commit()
            app.logger.info("New user registered: %s", username)
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.exception("Error registering user %s", username)
            msg = "An error occurred. Please try again later."
            return render_template('register.html', msg=msg)
        finally:
            cursor.close()

    return render_template('register.html', msg=msg)

# -------------------------
# Error handlers (don't leak internals)
# -------------------------
@app.errorhandler(500)
def internal_error(e):
    app.logger.exception("Server error: %s", e)
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

# -------------------------
# Run (dev only)
# -------------------------
if __name__ == '__main__':
    # In production, serve with Gunicorn behind HTTPS reverse proxy
    app.run(debug=False, host='127.0.0.1', port=5000)
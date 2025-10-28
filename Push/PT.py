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
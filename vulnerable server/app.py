# import flask library
# step 1: install flask.
# to import the flasks scripts, 

from flask import Flask

# the line tells python to import the flask class from the library of the already installed framework (flask)
# this should server as the Web Server Gateway Interface

app = Flask(__name__)

# Project here is a variable that has been declared to define the site,
# Flask is the framework where the resource (_name_) is derived from. 


# Logout Route (/logout): ends the session and redirects to the login page.
def logout():
    pass
# setup flask app to access route path

@app.route('/')

# this line tells the framework what to do when someone visits "/" (the homepage).

def home():
    return 'Welcome to my page Mr Ephraim!'

if __name__ == '__main__':
    app.run(debug=True)

# Running the App: the app runs in debug mode, enabling easy debugging during development.





# Note: This code is intentionally vulnerable for educational purposes. In a production environment, ensure to implement proper security measures such as password hashing, prepared statements to prevent SQL injection, and input validation.
# it would be Running on http://127.0.0.1:5000 becuase it's built to run via that route on the framework (flask)

# Running the App: the app runs in debug mode, enabling easy debugging during development.



@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
       
       
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        



    return render_template('register.html', msg=msg)

if __name__ == '__main__':
    

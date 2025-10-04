# import flask library
# step 1: install flask.
# to import the flasks scripts, 

from flask import Flask

# the line tells python to import the flask class from the library of the already installed framework (flask)
# this should server as the Web Server Gateway Interface

Project = Flask(__name__)

# Project here is a variable that has been declared to define the site,
# Flask is the framework where the resource (_name_) is derived from. 


# setup flask app to access route path

@Project.route('/')

# this line tells the framework what to do when someone visits "/" (the homepage).

def home():
    return 'Welcome to my page Mr Ephraim!'

if __name__ == '__main__':
    Project.run(debug=True)

# it would be Running on http://127.0.0.1:5000 becuase it's built to run via that route on the framework (flask)



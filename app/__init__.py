# File: __init__.py
#
# Description: Sets "app" folder as a package, initializes a Flask application 

from flask import Flask

app = Flask(__name__)

from app import routes
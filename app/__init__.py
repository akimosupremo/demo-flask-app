# File: __init__.py
#
# Description: Sets "app" folder as a package, initializes a Flask application 

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from sqlalchemy import MetaData
import mysql.connector

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

config = {
  'user': 'root',
  'password': 'root',
  'host': '127.0.0.1',
  'port': 8889,
  'database': 'DemoFlaskApp',
  'raise_on_warnings': True
}

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**config)

# a dictionary to define names for various db metadata
# e.g. primary key (pk), foreign key (fk)
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(app=app, metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate(app, db, render_as_batch=True)

# simple connection
cnx = mysql.connector.connect(**config)

# connection pool is a cache of database connections 
cnxpool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "mypool", pool_size = 5, **config)

from app import routes
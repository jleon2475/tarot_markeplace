from flask import Flask
from .extension import mysql

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')

    mysql.init_app(app)

    return app
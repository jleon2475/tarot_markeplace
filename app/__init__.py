from flask import Flask
from .extension import mysql, socketio
from .routes.auth import auth
from .routes.admin import admin
from .routes.cliente import cliente
from .routes.psychic import psychic
from .routes.wall import wall_bp
from . import socket_events


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')
    
    app.secret_key="clave_super_secreta"

    mysql.init_app(app)
    socketio.init_app(app)

    app.register_blueprint(auth)
    app.register_blueprint(cliente)
    app.register_blueprint(psychic)
    app.register_blueprint(admin)
    app.register_blueprint(wall_bp)  

    from . import socket_events    

    return app
    
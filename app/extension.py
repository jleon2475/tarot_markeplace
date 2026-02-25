from flask_mysqldb import MySQL
from flask_socketio import SocketIO

mysql = MySQL()
socketio = SocketIO(cors_allowed_origins="*", manage_session=False)
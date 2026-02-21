from app.extension import mysql
from werkzeug.security import generate_password_hash
import MySQLdb.cursors

class User:

    @staticmethod
    def create(name,email,password, role):
        hashed_password = generate_password_hash(password)        
        cur = mysql.connection.cursor()       

        cur.execute("INSERT INTO users(name, email, password, role) VALUES (%s,%s,%s,%s)", (name,email,hashed_password,role))
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_by_email(email):
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        return user
    
    @staticmethod
    def get_by_id(id):
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE id = %s", (id,))
        user = cur.fetchone()
        cur.close()
        return user
    
    @staticmethod
    def update(user_id,name,email,role):
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("UPDATE users SET name=%s,email=%s,role=%s WHERE id=%s",(name,email,role,user_id))
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def delete(user_id):
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_all():
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT id,name,email,role FROM users")
        users = cur.fetchall()
        cur.close()
        return users
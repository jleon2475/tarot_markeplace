from app import create_app
from app.extension import mysql
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    cur = mysql.connection.cursor()
    hashed = generate_password_hash("12345")
    cur.execute("""
                INSERT INTO users (name,email,password,role) VALUE (%s,%s,%s,%s)
                """, ("Admin","admin@gmail.com",hashed,"admin"))
    mysql.connection.commit()
    cur.close()

    print("Admin creado correctamente")
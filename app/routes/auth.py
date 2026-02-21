from flask import Blueprint, render_template, redirect, request, session, url_for
from app.models.user import User
from werkzeug.security import check_password_hash, generate_password_hash

auth = Blueprint('auth',__name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        User.create(
            request.form['name'],
            request.form['email'],
            request.form['password'],
            request.form['role']
        )
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.get_by_email(request.form['email'])
        
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session ['user_role'] = user['role']

            if session['user_role'] == 'admin':
                return redirect (url_for('admin.dashboard_admin'))
            elif session['user_role'] == 'psychic':
                return redirect(url_for('psychic.dashboard_psychic'))
            else:
                return redirect(url_for('cliente.dashboard_cliente'))
    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
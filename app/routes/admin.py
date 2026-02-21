from flask import Blueprint, render_template, request, redirect, url_for
from ..utils.decorators import login_required, role_required
from ..extension import mysql
from ..models.user import User

admin = Blueprint('admin', __name__,url_prefix='/admin')

@admin.route('/dashboard')
@login_required
@role_required('admin')
def dashboard_admin():
    return redirect(url_for('admin.users'))

@admin.route('users/agregar', methods=['GET','POST'])
@login_required
@role_required('admin')
def create():
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        User.create(name, email, password, role)
        return redirect(url_for('admin.users'))
    return render_template('/admin/create_user.html')
    

@admin.route('/users')
@login_required
@role_required('admin')
def users():
    users = User.get_all()
    return render_template('/admin/users.html', users=users)

@admin.route('users/edit/<int:user_id>', methods=['GET','POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = User.get_by_id(user_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']

        User.update(user_id, name, email, role)

        return redirect(url_for('admin.users'))
    return render_template('/admin/edit_user.html', user = user)

@admin.route('users/delete/<int:user_id>', methods=['GET','POST'])
@login_required
@role_required('admin')  
def delete(user_id):
    user = User.get_by_id(user_id)
    user = User.delete(user_id)
    return redirect(url_for('admin.users'))


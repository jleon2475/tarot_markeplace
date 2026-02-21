from flask import Blueprint, session, redirect, render_template
from ..utils.decorators import login_required,role_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/cliente')
@login_required
def dashboard():
    return render_template('cliente/dashboard.html')

@user_bp.route('/psychic')
@login_required
def dashboard():
    return render_template('psychic/dashboard.html')

@user_bp.route('/admin')
@login_required
@role_required('admin')
def admin():
    return render_template('admin/dashboard.html')
from flask import Blueprint, render_template
from ..utils.decorators import login_required, role_required
from ..extension import mysql

cliente = Blueprint('cliente', __name__,url_prefix='/cliente')

@cliente.route('/dashboard')
@login_required
@role_required('cliente')
def dashboard_cliente():
    return render_template('/cliente/dashboard.html')


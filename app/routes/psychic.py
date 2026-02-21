from flask import Blueprint, render_template
from ..utils.decorators import login_required, role_required
from ..extension import mysql

psychic = Blueprint('psychic', __name__,url_prefix='/psychic')

@psychic.route('/dashboard')
@login_required
@role_required('psychic')
def dashboard_psychic():
    return render_template('/psychic/dashboard.html')


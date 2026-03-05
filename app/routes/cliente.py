from flask import Blueprint, render_template, jsonify
from ..utils.decorators import login_required, role_required
from ..extension import mysql

cliente = Blueprint('cliente', __name__,url_prefix='/cliente')

@cliente.route('/dashboard')
@login_required
@role_required('cliente')
def dashboard_cliente():
    return render_template('/cliente/dashboard.html')

@cliente.route('/get_cards')
@login_required
@role_required('cliente')
def get_cards():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id,name,image FROM tarot_cards")
    cards = cur.fetchall()
    cur.close()
    return jsonify(cards)
from flask import Blueprint, render_template, jsonify, session
from ..utils.decorators import login_required, role_required
from ..extension import mysql

cliente = Blueprint('cliente', __name__,url_prefix='/cliente')

@cliente.route('/dashboard')
@login_required
@role_required('cliente')
def dashboard_cliente():
    user_name = session.get('user_name')
    return render_template('/cliente/dashboard.html', user_name=user_name)

@cliente.route('/get_cards')
@login_required
@role_required('cliente')
def get_cards():
    
    cur = mysql.connection.cursor()
    #Selecciona tres cartas al azar
    cur.execute("SELECT id,name,image FROM tarot_cards ORDER BY RAND() LIMIT 3")
    
    cards = cur.fetchall()
    cur.close()

    cards_data = []

    for card in cards:
        cards_data.append({
            "id": card[0],
            "name":card[1],
            "image":card[2]
        })
    
    return jsonify(cards_data)
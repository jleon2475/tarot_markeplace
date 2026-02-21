from flask import Blueprint, render_template

wall_bp = Blueprint('wall',__name__)

@wall_bp.route('/')
def index():
    return render_template('index.html')
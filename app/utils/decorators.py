from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args,**kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if session['user_role'] != role:
                return "Acceso No Autorizado", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
        
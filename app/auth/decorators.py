from flask import redirect, url_for
from flask_login import current_user
from functools import wraps


def disable_if_user_confirmed(f):
    @wraps(f)
    def decorated(*args, **kwargs):    
        if current_user.is_authenticated and current_user.confirmed:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated
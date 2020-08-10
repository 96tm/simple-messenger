from functools import wraps
from flask import redirect, request, url_for
from flask_login import current_user
from flask_socketio import disconnect


def authenticated_only(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not (current_user.is_authenticated and current_user.confirmed):
            disconnect()
        else:
            return f(*args, **kwargs)
    return decorated


def disable_if_unconfirmed(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not (current_user.is_authenticated and current_user.confirmed):
            return redirect(url_for('auth.unconfirmed'))
        else:
            return f(*args, **kwargs)
    return decorated
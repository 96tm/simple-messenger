from flask import abort
from flask_login import current_user
from functools import wraps
from models import Permissions


def permission_required(permissions):
    def decorator(function):
        @wraps
        def decorated(*args, **kwargs):
            if not current_user.has_permission(permission):
                abort(403)
            return function(*args, **kwargs)
        return decorated
    return decorator


def admin_required(function):
    return permission_required(Permissions.ADMINISTRATION)(function)

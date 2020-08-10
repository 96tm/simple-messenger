from flask_login import current_user
from flask import current_app, redirect, request, url_for


def before_auth_request():
    if (current_user.is_authenticated
        and not current_user.confirmed):
            view_name = current_app.view_functions[request.endpoint].__name__
            if view_name == 'unconfirmed':
                pass
            elif (request.blueprint not in ('auth', 'static')
                  or view_name not in ('confirm', 
                                       'resend_confirmation',
                                       'logout')):
                    return redirect(url_for('auth.unconfirmed'))
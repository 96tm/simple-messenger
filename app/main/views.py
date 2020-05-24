from flask import render_template, session, redirect, url_for
from . import main
from .. import database
from ..models import User
from flask_login import login_required, current_user
from datetime import datetime, timezone


@main.route('/')
@login_required
def index():
    return render_template('index.html', 
                           names = [user.username 
                                    for user 
                                    in current_user.contacts])


@main.before_app_request
def before_request():
    if current_user.is_authenticated and current_user.confirmed:
        current_user.last_seen = datetime.now(tz=timezone.utc)

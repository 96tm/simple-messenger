from flask import render_template, session, redirect, url_for
from . import main
from .. import database
from ..models import User
from flask_login import login_required, current_user
from datetime import datetime, timezone
from sqlalchemy import not_
from .forms import MessageForm


@main.route('/')
@login_required
def index():
    users = (User.query
            .filter(not_(User.id == current_user.id))
            .order_by(User.username).all())
    contacts = [user_contact.contact 
                for user_contact
                in current_user.contacts.all()]
    return render_template('index.html',
                           user = current_user,
                           users = users,
                           contacts = contacts,
                           form = MessageForm()
                           )


@main.before_app_request
def before_request():
    if current_user.is_authenticated and current_user.confirmed:
        current_user.last_seen = datetime.now(tz=timezone.utc)

from flask import render_template, session, redirect, url_for
from . import main
from .. import database
from ..models import User
from flask_login import login_required


@main.route('/')
@login_required
def index():
    return render_template('index.html')

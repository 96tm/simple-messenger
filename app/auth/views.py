from flask import render_template, flash, redirect, request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone
from sqlalchemy import or_
from . import auth
from .forms import LoginForm, RegistrationForm
from ..models import User
from .. import db


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next', url_for('main.index')))
        else:
            flash('Invalid email or password')
            form.data['password'] = ''
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('auth.login'))


@auth.route('/auth/signup', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.data['username']
        email = form.data['email']
        if User.query.filter_by(email=email).first():
            flash('This email is already registered')
            return render_template('auth/registration.html', form=form)
        elif User.query.filter_by(username=username).first():
            flash('This nickname is already taken')
            return render_template('auth/registration.html', form=form)
        user = User()
        user.username = username
        user.email = email
        user.registration_date = datetime.now(timezone.utc)
        user.password = form.data['password']
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('auth/registration.html', form=form)

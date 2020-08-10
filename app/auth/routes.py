from flask import current_app, Markup, render_template, flash, redirect
from flask import request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from smtplib import SMTPAuthenticationError
from . import auth
from .. import celery, database
from .decorators import disable_if_user_confirmed
from .forms import LoginForm, RegistrationForm
from ..tasks import send_email_task
from ..models import User


@auth.route('/unconfirmed')
@login_required
@disable_if_user_confirmed
def unconfirmed():
    return render_template('auth/unconfirmed.html', 
                           user=current_user)


@auth.route('/login', methods=['GET', 'POST'])
@disable_if_user_confirmed
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next_page = request.args.get('next')
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid email or password.')
            form.data['password'] = ''
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))


@auth.route('/signup', methods=['GET', 'POST'])
@disable_if_user_confirmed
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data.lower()
        if User.query.filter_by(username=username).first():
            flash('The username is already taken.')
            return render_template('auth/registration.html', form=form)
        elif User.query.filter_by(email=email).first():
            flash('The email is already registered.')
            return render_template('auth/registration.html', form=form)
        try:
            user = User()
            user.username = username
            user.email = email
            user.password = form.password.data
            database.session.add(user)
            database.session.commit()
            token = user.generate_confirmation_token()
            subject = (current_app.config['MAIL_SUBJECT_PREFIX'] 
                       + 'Registration confirmation')
            email_data = {'username':user.username,
                          'sender':current_app.config['MAIL_SENDER'],
                          'link':url_for('auth.confirm',
                                         token=token,
                                         _external=True)}
            task = send_email_task.delay(user.email,
                                         subject,
                                         'mail/registration_letter',
                                         email_data)
            login_user(user, remember=False)
            flash(Markup('A confirmation letter has been sent to '
                         + render_template('mail/mail_address.html',
                                           link=current_user.email)))
            return redirect(url_for('main.index'))
        except SMTPAuthenticationError:
            database.session.delete(user)
            database.session.commit()
            error_message = 'Server can\'t send the email, '\
                            'please contact our staff at '
            admin_email = current_app.config['ADMIN_MAIL']
            flash(Markup(error_message
                         + render_template('mail/mail_address.html',
                                           link=admin_email)),
                  category='error')
    return render_template('auth/registration.html', form=form)


@auth.route('/confirm/<token>')
@login_required
@disable_if_user_confirmed
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        database.session.commit()
        flash('Your account has been confirmed.')
    else:
        link = url_for('auth.resend_confirmation')
        flash(Markup('The confirmation link is invalid or has expired. '
                     + 'Please '
                     + render_template('link.html',
                                       link=link,
                                       link_text='click here') 
                     + ' to generate a new link.'),
              category='error')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
@disable_if_user_confirmed
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    subject = (current_app.config['MAIL_SUBJECT_PREFIX'] 
               + 'Registration confirmation')
    email_data = {'username':current_user.username,
                  'sender':current_app.config['MAIL_SENDER'],
                  'link':url_for('auth.confirm',
                                 token=token,
                                 _external=True)}
    try:
        task = send_email_task.delay(current_user.email,
                                     subject,
                                     'mail/registration_letter',
                                     email_data)
        flash(Markup('A new confirmation letter has been sent to '
                     + render_template('mail/mail_address.html',
                                       link=current_user.email)))
    except SMTPAuthenticationError:
        error_message = 'Server can\'t send the email, '\
                        'please contact our staff at '
        admin_email = current_app.config['ADMIN_MAIL']
        flash(Markup(error_message
                     + render_template('mail/mail_address.html',
                                       link=admin_email)),
              category='error')
    return redirect(url_for('main.index'))
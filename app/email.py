from flask import current_app, render_template
from flask_mail import Message
from . import mail
from threading import Thread


def send_async_email(app, message):
    with app.app_context():
        mail.send(message)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    message = Message(app.config['MAIL_SUBJECT_PREFIX'] + subject,
                      sender=app.config['MAIL_SENDER'],
                      recipients=[to])
    message.body = render_template(template + '.txt', **kwargs)
    message.html = render_template(template + '.html', **kwargs)
    thread = Thread(target=send_async_email, args=[app, message])
    thread.start()
    return thread

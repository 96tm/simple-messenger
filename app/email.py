from flask import current_app, render_template
from flask_mail import Message
from . import mail


def send_email(to, subject, template, email_data):
    app = current_app._get_current_object()
    username = email_data['username']
    link = email_data['link']
    sender = email_data['sender']
    message = Message(subject=subject,
                      sender=sender,
                      recipients=[to])
    message.body = render_template(template + '.txt', 
                                   username=username,
                                   link=link)
    message.html = render_template(template + '.html',
                                   username=username,
                                   link=link)
    with app.app_context():
        mail.send(message)
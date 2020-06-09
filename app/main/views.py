from flask import render_template, session, redirect, url_for
from . import main
from .. import database
from ..models import User, Message
from flask_login import login_required, current_user
from datetime import datetime, timezone
from sqlalchemy import not_, or_, and_
from .forms import MessageForm
from flask import jsonify, request, flash, abort


def get_messages(user, contact_id):
    contact = User.query.get_or_404(contact_id)
    messages = (database
                .session
                .query(Message)
                .filter(or_(and_(Message.sender == user,
                                    Message.recipient == contact),
                            and_(Message.sender == contact,
                                    Message.recipient == user)))
                .order_by(Message.message_date)
                .all())
    date_format = '%A, %B %d %Y %H:%M'
    messages = [{'text': message.text,
                 'timestamp': message.message_date.strftime(date_format),
                 'sender_username': message.sender.username} 
                for message in messages]
    # print(messages[0]['timestamp'].isoformat())
    return jsonify({'messages': messages,
                    'contact_username': contact.username,
                    'current_username': current_user.username
                   })


@main.route('/choose_contact', methods=['POST'])
@login_required
def choose_contact():
    if request.is_json and request.json and request.json['contact_id']:
        try:
            contact_id = int(request.json['contact_id'])
            json_messages = get_messages(current_user._get_current_object(),
                                         contact_id)
            session['current_contact_id'] = contact_id
            return json_messages
        except ValueError:
            print('Invalid contact')
    flash('Invalid contact')
    return jsonify({'messages': None})


@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    if request.is_json and request.json and request.json['message']:
        message = None
        try:
            text = request.json['message']
            recipient_id = int(request.json['recipient_id'])
            recipient = User.query.get(recipient_id)
            message = Message(text = text,
                              sender=current_user._get_current_object(),
                              recipient=recipient)
            database.session.add(message)
            database.session.commit()
        except ValueError:
            print('Invalid message data')
            abort(404)
    date_format = '%A, %B %d %Y %H:%M'
    message_dict = {
        'text': message.text,
        'timestamp': message.message_date.strftime(date_format),
        'sender_username': message.sender.username
    }
    return jsonify({'message': message_dict,
                    'current_username': current_user.username,
                    'contact_username': recipient.username})


@main.route('/')
@login_required
def index():
    users = (User.query
            .filter(not_(User.id == current_user.id))
            .order_by(User.username).all())
    contacts = (contact.contact for contact in current_user.contacts)
    current_contact_id = session.get('current_contact_id')
    messages = None
    if current_contact_id:
        messages = get_messages(current_user._get_current_object(), current_contact_id)
        print(messages.json)
    return render_template('index.html',
                           contacts = contacts,
                           users = users,
                           messages = messages,
                           current_contact_id=current_contact_id)


@main.before_app_request
def before_request():
    if current_user.is_authenticated and current_user.confirmed:
        current_user.last_seen = datetime.now(tz=timezone.utc)

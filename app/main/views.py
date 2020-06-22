from flask import render_template, session, redirect, url_for
from flask import jsonify, request, flash, abort, current_app
from . import main
from .. import database
from ..models import User, Message, Chat
from ..models import UserChatTable, Contact
from flask_login import login_required, current_user
from datetime import datetime, timezone
from sqlalchemy import not_, or_, and_
from .forms import MessageForm


def format_date(date):
    date_format = '%A, %B %d %Y %H:%M'
    return date.strftime(date_format)


def get_or_create_chat(chat_id):
    chat = Chat.query.get(chat_id).first()
    if not chat:
        chat = Chat()
        chat.add_user(user)
        chat.add_user(contact)
    return chat


def get_messages(chat):
    user = current_user._get_current_object()
    recipient_username = None
    if chat.is_group_chat:
        recipient = chat.users.filter(User.id != user.id).first()
        recipient_username = recipient.username

    query_to_update = (chat
                       .messages
                       .filter(and_(Message.sender != user,
                                    not_(Message.was_read))))

    messages = chat.messages.order_by(Message.date_created).all()

    Message.flush_messages(query_to_update)

    message_list = []
    for message in messages:
        sender = message.sender
        recipient = message.recipient
        sender_name = sender.username if sender else None
        recipient_name = recipient.username if recipient else None
        message_list.append({'text': message.text,
                             'date_created': format_date(message.date_created),
                             'sender_username': sender_name,
                             'recipient_username': recipient_name})

    return message_list


 # TODO optimize queries
@main.route('/add_contacts_and_chats', methods=['POST'])
@login_required
def add_contacts_and_chats():
    if request.is_json and request.json and request.json.get('user_ids'):
        try:
            added_chats = []
            new_contacts = []
            current = current_user._get_current_object()
            user_ids = [int(user_id) for user_id in request.json['user_ids']]
            chats = Chat.get_removed_chats(current, user_ids)
            for chat in chats:
                recipient = chat.users.filter(User.id != current.id).first()
                chat_data = {'chat_name': chat.name or recipient.username,
                             'chat_id': chat.id}
                added_chats.append(chat_data)
            for user_id in user_ids:
                user = User.query.get_or_404(user_id)
                if not current.has_contact(user):
                    new_contacts.append(user)
                chat = Chat.get_chat(current, user)
                if not chat:
                    chat = Chat()
                    database.session.add(chat)
                    chat.add_users([current, user])
                    database.session.commit()
                    chat_data = {'chat_name': chat.name or user.username,
                                'chat_id': chat.id}
                    added_chats.append(chat_data)
            current.add_contacts(new_contacts)
            print(added_chats)
            data = {'added_chats': added_chats}
            return jsonify(data)
        except ValueError:
            print('Invalid user')
    abort(404)


@main.route('/check_new_messages', methods=['POST'])
@login_required
def check_new_messages():
    if request.is_json and request.json and request.json.get('chat_id'):
        try:
            user = current_user._get_current_object()
            chat_id = int(request.json['chat_id'])
            chat = Chat.query.get_or_404(chat_id)
            chat_name = chat.name
            if not chat.is_group_chat:
                recipient = chat.users.filter(User.id != user.id).first()
                chat_name = recipient.username
            else:
                current_chat_name = chat.name
            messages = chat.messages.filter(Message.sender != user)

            messages_json = []
            for message in messages.all():
                sender = message.sender
                sender_username = sender.username if sender else None
                date_created = format_date(message.date_created)
                message_json = {'text': message.text,
                                'sender_username': sender_username,
                                'date_created': date_created}
                messages_json.append(message_json)
            Message.flush_messages(messages)
            data = {'messages': messages_json,
                    'current_username': user.username,
                    'chat_name': chat_name}
            return jsonify(data)
        except ValueError:
            print('Invalid contact')
    abort(404)


# change contact to chat
@main.route('/remove_chat', methods=['POST'])
@login_required
def remove_chat():
    if request.is_json and request.json and request.json.get('chat_id'):
        try:
            chat_id = int(request.json['chat_id'])
            chat = Chat.query.get_or_404(chat_id)
            current = current_user._get_current_object()
            session['current_chat_id'] = None

            Chat.mark_chats_as_removed(current, [chat])

            data = {'chat_id': str(chat_id)}
            return jsonify({'removed_chat': data})
        except ValueError:
            print('Invalid contact')
    abort(404)


@main.route('/choose_chat', methods=['POST'])
@login_required
def choose_chat():
    if request.is_json and request.json and request.json.get('chat_id'):
        try:
            chat_id = int(request.json['chat_id'])
            saved_chat_id = session.get('current_chat_id')
            if saved_chat_id == chat_id:
                session['current_chat_id'] = None
                return jsonify({'messages': [],
                                'chat_name': '',
                                'current_username': current_user.username})
            chat = Chat.query.get_or_404(chat_id)
            chat_name = chat.name
            if not chat_name:
                recipient = chat.users.filter(User.id != current_user.id).first()
                chat_name = recipient.username
            messages = get_messages(chat)
            session['current_chat_id'] = chat_id
            return jsonify({'messages': messages,
                            'chat_name': chat_name,
                            'current_username': current_user.username})
        except ValueError:
            print('Invalid chat')
    flash('Invalid chat')
    return jsonify({'messages': [],
                    'chat_name': '',
                    'current_username': ''})


# TODO
@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    if request.is_json and request.json and request.json['message']:
        message = None
        chat_name = None
        try:
            text = request.json['message']
            chat_id = int(request.json['chat_id'])
            chat = Chat.query.get_or_404(chat_id)
            recipient = None
            if not chat.is_group_chat:
                recipient = chat.users.filter(User.id != current_user.id).first()
                chat_name = recipient.username
            else:
                chat_name = chat.name
            message = Message(text = text,
                              sender=current_user._get_current_object(),
                              recipient=recipient,
                              chat=chat)
            database.session.add(message)
            database.session.commit()
        except ValueError:
            print('Invalid message data')
            abort(404)
    message_dict = {
        'text': message.text,
        'date_created': format_date(message.date_created),
        'sender_username': message.sender.username
    }
    return jsonify({'message': message_dict,
                    'current_username': current_user.username,
                    'chat_name': chat_name})


@main.route('/')
@login_required
def index():
    current = current_user._get_current_object()
    users = current.get_other_users()
    chats = current.get_available_chats()

    chat_list = []
    for chat in chats:
        if chat.is_group_chat:
            name = chat.name
        else:
            recipient = chat.users.filter(User.id != current_user.id).first()
            name = recipient.username
        chat_list.append({'name': name, 'chat_id': chat.id})
    messages = None
    current_chat_id = None
    current_chat_name = None
    if session.get('current_chat_id'):
        current_chat_id = session.get('current_chat_id')
    if current_chat_id and Chat.query.get(current_chat_id):
        chat = Chat.query.get_or_404(current_chat_id)
        messages = get_messages(chat)
        if not chat.is_group_chat:
            recipient = chat.users.filter(User.id != current_user.id).first()
            current_chat_name = recipient.username
        else:
            current_chat_name = chat.name

    return render_template('index.html',
                           chats = chat_list,
                           users = users,
                           messages = messages,
                           current_chat_id=current_chat_id,
                           current_chat_name=current_chat_name)


@main.before_app_request
def before_request():
    if current_user.is_authenticated and current_user.confirmed:
        current_user.last_seen = datetime.now(tz=timezone.utc)

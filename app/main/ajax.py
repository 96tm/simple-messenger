from . import main
from .. import database
from ..models import Chat, Contact, Message 
from ..models import UserChatTable, User

from datetime import datetime, timezone
from flask import current_app, escape, request
from flask import jsonify, session
from flask_login import current_user, login_required
import json


def generate_json_response(status_code, data=None):
    """
    Generate HTTP response with given status_code
    and data jsonified

    :param status_code: int, HTTP status code
    :param data: object to be sent
    """
    json_response = current_app.response_class(
        response=json.dumps(data),
        status=status_code,
        mimetype='application/json'
    )
    return json_response


@main.route('/add_contacts_and_chats', methods=['POST'])
@login_required
def add_contacts_and_chats():
    if request.is_json and request.json and request.json.get('user_ids'):
        try:
            new_contacts = []
            user_ids = [int(user_id) for user_id in request.json['user_ids']]
            chats = Chat.get_removed_chats(current_user, user_ids)
            added_chats = [{'chat_name': chat.get_name(current_user),
                            'chat_id': str(chat.id)}
                           for chat
                           in chats]
            for user_id in user_ids:
                user = User.query.get_or_404(user_id)
                if not current_user.has_contact(user):
                    new_contacts.append(user)
                chat = Chat.get_chat([current_user, user])
                if not chat:
                    chat = Chat()
                    database.session.add(chat)
                    chat.add_users([current_user, user])
                    database.session.commit()
                    chat_data = {'chat_name': chat.get_name(current_user),
                                 'chat_id': str(chat.id)}
                    added_chats.append(chat_data)
            current_user.add_contacts(new_contacts)
            data = {'added_chats': added_chats}
            return jsonify(data)
        except ValueError:
            pass
    return generate_json_response(400)


@main.route('/check_new_messages', methods=['POST'])
@login_required
def check_new_messages():
    if (request.is_json 
        and request.json 
        and request.json.get('chat_id') is not None):
            try:
                chat_id = int(request.json['chat_id'])
                chat = Chat.query.get_or_404(chat_id)
                message_dict_list = current_user.get_unread_messages(chat)
                data = {'messages': message_dict_list,
                        'current_username': current_user.username}
                return jsonify(data)
            except (ValueError, OverflowError):
                return generate_json_response(400)
    return generate_json_response(404)


@main.route('/load_messages', methods=['POST'])
@login_required
def load_messages():
    if (request.is_json 
        and request.json 
        and request.json.get('chat_id') is not None):
            try:
                chat_id = int(request.json['chat_id'])
                chat = Chat.query.get_or_404(chat_id)
                message_dict_list = current_user.get_messages(chat)
                data = {'messages': message_dict_list,
                        'current_username': current_user.username}
                return jsonify(data)
            except (ValueError, OverflowError):
                return generate_json_response(400)
    return generate_json_response(404)


@main.route('/choose_chat', methods=['POST'])
@login_required
def choose_chat():
    if (request.is_json 
        and request.json 
        and request.json.get('chat_id') is not None):
            try:
                chat_id = int(request.json['chat_id'])
                saved_chat_id = session.get('current_chat_id')
                username = current_user.username
                if saved_chat_id == chat_id:
                    session['current_chat_id'] = None
                    return jsonify({'messages': [],
                                    'chat_name': '',
                                    'current_username': username})
                chat = Chat.query.get_or_404(chat_id)
                message_dict_list = current_user.get_messages(chat)
                session['current_chat_id'] = chat_id
                return jsonify({'messages': message_dict_list,
                                'chat_name': chat.get_name(current_user),
                                'current_username': current_user.username})
            except (ValueError, OverflowError):
                return generate_json_response(400)
    return generate_json_response(404)


@main.route('/load_chats', methods=['POST'])
@login_required
def load_chats():
    if (request.is_json 
        and request.json 
        and request.json.get('page_number') is not None):
            try:
                page_number = int(request.json['page_number'])
                chats = (current_user.get_available_chats_query()
                        .paginate(page_number, 
                                current_app.config['CHATS_PER_PAGE'],
                                error_out=False)
                        .items)
                chats_dict_list = [{'chat_name': chat.get_name(current_user),
                                    'chat_id': str(chat.id)}
                                   for chat
                                   in chats]
                return jsonify({'chats': chats_dict_list})
            except (ValueError, OverflowError):
                pass
    return generate_json_response(400)


@main.route('/load_users', methods=['POST'])
@login_required
def load_users():
    if (request.is_json 
        and request.json 
        and request.json.get('page_number') is not None):
            try:
                page_number = int(request.json['page_number'])
                added_users = (current_user
                              .get_other_users_query()
                              .paginate(page_number,
                                        current_app.config["USERS_PER_PAGE"],
                                        error_out=False)
                              .items
                            )
                added_users_dict_list = [{'username': user.username,
                                        'user_id': user.id} 
                                        for user in added_users]
                return jsonify({'added_users': added_users_dict_list})
            except (ValueError, OverflowError):
                return generate_json_response(400)
    return generate_json_response(404)


@main.route('/remove_chat', methods=['POST'])
@login_required
def remove_chat():
    if (request.is_json 
        and request.json 
        and request.json.get('chat_id') is not None):
            try:
                chat_id = int(request.json['chat_id'])
                chat = Chat.query.get_or_404(chat_id)
                session['current_chat_id'] = None
                Chat.mark_chats_as_removed(current_user, [chat])
                data = {'chat_id': str(chat_id)}
                return jsonify({'removed_chat': data})
            except (ValueError, OverflowError):
                return generate_json_response(400)
    return generate_json_response(404)


@main.route('/search_chats', methods=['POST'])
@login_required
def search_chats():
    if request.is_json and request.json and request.json.get('chat_name'):
        try:
            chat_name = escape(str(request.json['chat_name']))
            chat_name = chat_name[:current_app.config['MAX_STRING_LENGTH']]
            page_number = int(request.json['page_number'])
            
            chats = (Chat.search_chats_query(chat_name, current_user)
                     .paginate(page_number, 
                               current_app.config['CHATS_PER_PAGE'],
                               error_out=False)
                     .items)
            chats_dict_list = [{'chat_name': chat.get_name(current_user),
                                'chat_id': str(chat.id)}
                               for chat 
                               in chats]
            return jsonify({'found_chats': chats_dict_list})
        except (ValueError, OverflowError):
            generate_json_response(400)
    return generate_json_response(404)


@main.route('/search_users', methods=['POST'])
@login_required
def search_users():
    if request.is_json and request.json and request.json.get('username'):
        try:
            username = escape(str(request.json['username']))
            username = username[:current_app.config['MAX_STRING_LENGTH']]
            page_number = int(request.json['page_number'])
            users = (current_user.
                     search_users_query(username, 
                                        current_user.get_other_users_query())
                    .paginate(page_number,
                              current_app.config['USERS_PER_PAGE'],
                              error_out=False)
                    .items)
            users_dict_list = [{'username': user.username,
                                'user_id': user.id} for user in users]
            return jsonify({'found_users': users_dict_list})
        except (ValueError, OverflowError):
            return generate_json_response(400)
    return generate_json_response(404)


@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    if (request.is_json 
        and request.json 
        and request.json.get('message') is not None):
            try:
                message = None
                recipient = None
                text = escape(str(request.json['message']))
                chat_id = int(request.json['chat_id'])
                chat = Chat.query.get_or_404(chat_id)
                if not chat.is_group_chat:
                    recipient = (chat
                                .users
                                .filter(User.id != current_user.id)
                                .first())
                message = Message(text=text,
                                  sender=current_user,
                                  recipient=recipient,
                                  chat=chat)
                database.session.add(message)
                database.session.commit()
            except (ValueError, OverflowError):
                return generate_json_response(400)
    message_dict = {
        'text': message.text,
        'date_created': message.date_created,
        'sender_username': message.sender.username
    }
    return jsonify({'message': message_dict,
                    'current_username': current_user.username,
                    'chat_name': chat.get_name(current_user)})

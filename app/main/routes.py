import gevent, traceback
from gevent.pool import Pool
from datetime import datetime, timezone
from flask import copy_current_request_context, current_app
from flask import escape, redirect, url_for
from flask import render_template, request, session
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound

from . import main
from .decorators import authenticated_only, disable_if_unconfirmed
from .forms import ChatSearchForm, MessageForm, UserSearchForm
from .. import database, socket_io
from ..models import Chat, Message, User


USER_WEBSOCKET_MAPPING = dict()
CHAT_UPDATES_POOL = Pool()


def log_exception():
    traceback.print_exc()


@socket_io.on('search_users')
@authenticated_only
def search_users(data):
    try:
        username = str(escape(data['username']))
        username = username[:current_app.config['MAX_STRING_LENGTH']]
        page_number = int(data['page_number'])
        users = (current_user
                 .search_users_query(username, 
                                     current_user.get_other_users_query())
                 .paginate(page_number,
                           current_app.config['USERS_PER_PAGE'],
                           error_out=False)
                 .items)
        users_dict_list = [{'username': user.username,
                            'user_id': user.id} for user in users]
        socket_io.emit('search_users',
                       {'found_users': users_dict_list,
                        'page_number': str(page_number)},
                       room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (OverflowError, ValueError):
        log_exception()


@socket_io.on('load_messages')
@authenticated_only
def load_messages(data):
    try:
        chat_id = int(data['chat_id'])
        chat = Chat.query.get_or_404(chat_id)
        message_dict_list = current_user.get_messages(chat)
        socket_io.emit('load_messages',
                        {'messages': message_dict_list,
                         'current_username': current_user.username},
                        room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (AttributeError, OverflowError, ValueError, NotFound):
        log_exception()


@socket_io.on('load_users')
@authenticated_only
def load_users(data):
    try:
        page_number = int(data['page_number'])
        clear_area = bool(data['clear_area'])
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
        socket_io.emit('load_users',
                       {'added_users': added_users_dict_list,
                        'clear_area': clear_area},
                       room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (ValueError, OverflowError):
        log_exception()


@socket_io.on('search_chats')
@authenticated_only
def search_chats(data):
    try:
        chat_name = str(escape(data['chat_name']))
        chat_name = chat_name[:current_app.config['MAX_STRING_LENGTH']]
        page_number = int(data['page_number'])

        chats = (Chat.search_chats_query(chat_name, current_user)
                 .paginate(page_number, 
                           current_app.config['CHATS_PER_PAGE'],
                           error_out=False)
                 .items)
        chats_dict_list = [{'chat_name': chat.get_name(current_user),
                            'chat_id': str(chat.id)}
                            for chat 
                            in chats]
        socket_io.emit('search_chats',
                       {'found_chats': chats_dict_list,
                        'page_number': str(page_number)},
                       room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (LookupError, ValueError, OverflowError):
        log_exception()


@socket_io.on('load_chats')
@authenticated_only
def load_chats(data):
    try:
        page_number = int(data['page_number'])
        chats = (current_user.get_available_chats_query()
                 .paginate(page_number, 
                           current_app.config['CHATS_PER_PAGE'],
                           error_out=False)
                 .items)
        chats_dict_list = [{'chat_name': chat.get_name(current_user),
                            'chat_id': str(chat.id)}
                            for chat
                            in chats]
        socket_io.emit('load_chats', 
                       {'chats': chats_dict_list,
                        'page_number': str(page_number)},
                       room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (LookupError, ValueError, OverflowError):
        log_exception()


@socket_io.on('remove_chat')
@authenticated_only
def remove_chat(data):
    try:
        chat_id = int(data['chat_id'])
        chat = Chat.query.get_or_404(chat_id)
        session[(current_user.id, 'current_chat_id')] = None
        current_user.mark_chats_as_removed([chat])
        socket_io.emit('remove_chat',
                       {'chat_id': str(chat_id)},
                       room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (AttributeError, LookupError, ValueError, OverflowError):
        log_exception()
    except IntegrityError as e:
        database.session.rollback()
        log_exception()


@socket_io.on('connect')
@authenticated_only
def save_room():
    global CHAT_UPDATES_POOL, USER_WEBSOCKET_MAPPING
    if current_user and not current_user.is_anonymous:
        USER_WEBSOCKET_MAPPING[current_user.id] = request.sid
        data = current_user.get_updated_chats(current_user, session)
        if data:
            worker = (gevent
                      .spawn(copy_current_request_context(send_update),
                             data=data,
                             sid=request.sid))
            CHAT_UPDATES_POOL.add(worker)


@socket_io.on('disconnect')
@authenticated_only
def disconnect():
    global CHAT_UPDATES_POOL, USER_WEBSOCKET_MAPPING
    if current_user and not current_user.is_anonymous:
        if current_user.id in USER_WEBSOCKET_MAPPING:
            del USER_WEBSOCKET_MAPPING[current_user.id]


@socket_io.on('send_message')
@authenticated_only
def send_message(data):
    global CHAT_UPDATES_POOL
    try:
        message = None
        text = str(escape(data['message_text']).rstrip())
        if not text:
            return
        chat_id = int(data['chat_id'])
        chat = Chat.query.get_or_404(chat_id)
        recipient = None
        if not chat.is_group_chat:
            recipient = (chat
                        .users
                        .filter(User.id != current_user.id)
                        .first())
        message = Message(text=text,
                          sender=current_user,
                          recipient=recipient,
                          chat=chat)
        chat.date_modified = datetime.now(tz=timezone.utc)
        database.session.add_all([message, chat])
        database.session.commit()
        recipients = (chat
                      .users
                      .filter(User.username != current_user.username)
                      .all())
        message_dict = {
            'text': message.text,
            'date_created': message.date_created.isoformat(),
            'sender_username': message.sender.username
        }
        socket_io.emit('send_message', 
                       {'message': message_dict,
                        'current_username': current_user.username,
                        'chat_name': chat.get_name(current_user)},
                       room=USER_WEBSOCKET_MAPPING[current_user.id])
        for recipient in recipients:
            recipient.unmark_chats_as_removed([chat])
            if recipient.id in USER_WEBSOCKET_MAPPING:
                sid = USER_WEBSOCKET_MAPPING[recipient.id]
                data = recipient.get_updated_chats(current_user, 
                                                   session)
                if data:
                    worker = (gevent
                             .spawn(copy_current_request_context(send_update),
                                    data=data,
                                    sid=sid))
                    CHAT_UPDATES_POOL.add(worker)
    except (AttributeError, LookupError, 
            OverflowError, ValueError, NotFound):
        log_exception()
    except IntegrityError:
        database.session.rollback()
        log_exception()


@socket_io.on('flush_messages')
@authenticated_only
def flush_messages(data):
    try:
        chat_id = int(data['chat_id'])
        chat = Chat.query.get_or_404(chat_id)
        Message.flush_messages(current_user.get_unread_messages_query(chat))
    except (AttributeError, OverflowError, ValueError, NotFound):
        log_exception()

@socket_io.on('choose_chat')
@authenticated_only
def choose_chat(data):
    try:
        chat_id = int(data['chat_id'])
        saved_chat_id = session.get((current_user.id,'current_chat_id'))
        if saved_chat_id == chat_id:
            session[(current_user.id,'current_chat_id')] = None
            socket_io.emit('choose_chat',
                           {'messages':[],
                            'chat_name': '',
                            'chat_id': str(chat_id),
                            'current_username': current_user.username},
                           room=USER_WEBSOCKET_MAPPING[current_user.id])
        else:
            chat = Chat.query.get_or_404(chat_id)
            message_dict_list = current_user.get_messages(chat)
            Message.flush_messages(current_user
                                   .get_unread_messages_query(chat))
            session[(current_user.id, 'current_chat_id')] = chat_id
            socket_io.emit('choose_chat', 
                            {'messages': message_dict_list,
                             'chat_name': chat.get_name(current_user),
                             'chat_id': str(chat.id),
                             'current_username': current_user.username},
                            room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (OverflowError, ValueError, NotFound):
        log_exception()


@socket_io.on('add_contacts_and_chats')
@authenticated_only
def add_contacts_and_chats(data):
    try:
        new_contacts = []
        user_ids = [int(user_id) for user_id in data['user_ids']]
        removed_query = current_user.get_removed_chats_query(user_ids)
        removed_chats = removed_query.all()
        current_user.unmark_chats_as_removed(removed_query)
        added_chats = []
        for chat in removed_chats:
            added_chats.append({'chat_name': chat.get_name(current_user),
                                'chat_id': str(chat.id)})
            chat.date_modified = datetime.now(tz=timezone.utc)
            database.session.add(chat)
        for user in User.query.filter(User.id.in_(user_ids)):
            if not current_user.has_contact(user):
                new_contacts.append(user)
            chat = Chat.get_chat([current_user, user])
            if not chat:
                chat = Chat()
                database.session.add(chat)
                chat.add_users([current_user, user])
                user.mark_chats_as_removed([chat])
                database.session.commit()
                chat_data = {'chat_name': chat.get_name(current_user),
                             'chat_id': str(chat.id)}
                added_chats.append(chat_data)
        socket_io.emit('add_contacts_and_chats',
                       {'added_chats': added_chats},
                       room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (ValueError, TypeError):
        log_exception
    except IntegrityError:
        database.session.rollback()
        log_exception


@main.route('/')
@login_required
@disable_if_unconfirmed
def index():
    current = current_user._get_current_object()
    users = current.get_other_users_query()
    chats = current.get_available_chats_query()
    users = (users
             .paginate(1, per_page=current_app.config["USERS_PER_PAGE"],
                       error_out=False)
             .items)
    chat_list = []
    current_chat_id = session.get((current_user.id, 'current_chat_id'))
    for chat in chats:
        recipient = chat.users.filter(User.id != current_user.id).first()
        name = chat.name or recipient.username
        unread_messages_count = 0
        if chat.id == current_chat_id:
            Message.flush_messages(current.get_unread_messages_query(chat))
        else:
            unread_messages_count = (current_user
                                    .get_unread_messages_query(chat)
                                    .count())
        chat_list.append({'name': name,
                          'chat_id': chat.id,
                          'unread_messages_count': unread_messages_count})
    current_chat_id = None
    current_chat_name = None
    if session.get((current_user.id, 'current_chat_id')):
        current_chat_id = session.get((current_user.id, 'current_chat_id'))
    if current_chat_id:
        try:
            chat = Chat.query.get_or_404(current_chat_id)
            current_chat_name = chat.get_name(current)
        except NotFound:
            current_chat_id = None
    return render_template('main/index.html',
                           chats = chat_list,
                           current_chat_id=current_chat_id,
                           current_chat_name=current_chat_name,
                           message_form = MessageForm(),
                           chat_search_form=ChatSearchForm(),
                           user_search_form=UserSearchForm(),
                           users = users,
                          )


@authenticated_only
def send_update(data, sid):
    socket_io.emit('chat_updated', data, room=sid)
from datetime import datetime, timezone
from flask import abort, copy_current_request_context, current_app, escape
from flask import render_template, request, session
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from . import main
from .forms import ChatSearchForm, MessageForm, UserSearchForm
from .. import database, socket_io
from ..models import Chat, Message, RemovedChat, User

import gevent
from gevent.pool import Pool


USER_WEBSOCKET_MAPPING = dict()
CHAT_UPDATES_POOL = Pool()


@socket_io.on('search_users')
def search_users(data):
    try:
        username = escape(str(data['username']))
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
    except (ValueError, OverflowError):
        abort(404)


@socket_io.on('load_messages')
def load_messages(data):
    try:
        chat_id = int(data['chat_id'])
        chat = Chat.query.get_or_404(chat_id)
        message_dict_list = current_user.get_messages(chat)
        socket_io.emit('load_messages',
                        {'messages': message_dict_list,
                        'current_username': current_user.username},
                        room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (ValueError, OverflowError):
        abort(404)


@socket_io.on('load_users')
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
        abort(404)


@socket_io.on('search_chats')
def search_chats(data):
    try:
        chat_name = escape(str(data['chat_name']))
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
        abort(404)


@socket_io.on('load_chats')
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
        abort(404)


@socket_io.on('remove_chat')
def remove_chat(data):
    try:
        chat_id = int(data['chat_id'])
        chat = Chat.query.get_or_404(chat_id)
        session['current_chat_id'] = None
        current_user.mark_chats_as_removed([chat])
        socket_io.emit('remove_chat',
                       {'chat_id': str(chat_id)},
                       room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (LookupError, ValueError, OverflowError, IntegrityError):
        abort(404)


@socket_io.on('connect')
def save_room():
    global CHAT_UPDATES_POOL, USER_WEBSOCKET_MAPPING
    if current_user and not current_user.is_anonymous:
        USER_WEBSOCKET_MAPPING[current_user.id] = request.sid
        data = get_updated_chats(current_user)
        if data:
            worker = (gevent
                      .spawn(copy_current_request_context(send_update),
                             data=data,
                             sid=request.sid))
            CHAT_UPDATES_POOL.add(worker)


@socket_io.on('disconnect')
def test_disconnect():
    global CHAT_UPDATES_POOL, USER_WEBSOCKET_MAPPING
    if current_user and not current_user.is_anonymous:
        del USER_WEBSOCKET_MAPPING[current_user.id]


@socket_io.on('send_message')
def send_message(data):
    global CHAT_UPDATES_POOL
    try:
        message = None
        text = escape(str(data['message_text']).rstrip())
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
        for recipient in recipients:
            recipient.unmark_chats_as_removed([chat])
            if recipient.id in USER_WEBSOCKET_MAPPING:
                sid = USER_WEBSOCKET_MAPPING[recipient.id]
                data = get_updated_chats(recipient)
                if data:
                    worker = (gevent
                             .spawn(copy_current_request_context(send_update),
                                    data=data,
                                    sid=sid))
                    CHAT_UPDATES_POOL.add(worker)
    except (ValueError, OverflowError):
        abort(404)
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


@socket_io.on('flush_messages')
def flush_messages(data):
    try:
        chat_id = int(data['chat_id'])
        chat = Chat.query.get_or_404(chat_id)
        Message.flush_messages(current_user.get_unread_messages_query(chat))
    except (ValueError, OverflowError):
        abort(404)


@socket_io.on('choose_chat')
def choose_chat(data):
    try:
        chat_id = int(data['chat_id'])
        saved_chat_id = session.get('current_chat_id')
        if saved_chat_id == chat_id:
            session['current_chat_id'] = None
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
            session['current_chat_id'] = chat_id
            socket_io.emit('choose_chat', 
                            {'messages': message_dict_list,
                             'chat_name': chat.get_name(current_user),
                             'chat_id': str(chat.id),
                             'current_username': current_user.username},
                            room=USER_WEBSOCKET_MAPPING[current_user.id])
    except (ValueError, OverflowError):
        abort(404)


@socket_io.on('add_contacts_and_chats')
def add_contacts_and_chats(data):
    try:
        new_contacts = []
        user_ids = [int(user_id) for user_id in data['user_ids']]
        removed_query = current_user.get_removed_chats_query(user_ids)
        removed_chats = removed_query.all()
        current_user.unmark_chats_as_removed(removed_query)
        added_chats = [{'chat_name': chat.get_name(current_user),
                        'chat_id': str(chat.id)}
                        for chat
                        in removed_chats]
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
        abort(404)


@main.route('/')
@login_required
def index():
    current = current_user._get_current_object()
    users = current.get_other_users_query()
    chats = current.get_available_chats_query()
    users = (users
             .paginate(1, 
                       per_page=current_app
                                .config["USERS_PER_PAGE"],
                       error_out=False)
             .items)
    chat_list = []
    current_chat_id = session.get('current_chat_id')
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
    if session.get('current_chat_id'):
        current_chat_id = session.get('current_chat_id')
    if current_chat_id and Chat.query.get(current_chat_id):
        chat = Chat.query.get_or_404(current_chat_id)
        current_chat_name = chat.get_name(current)
    return render_template('main/index.html',
                           chats = chat_list,
                           current_chat_id=current_chat_id,
                           current_chat_name=current_chat_name,
                           message_form = MessageForm(),
                           chat_search_form=ChatSearchForm(),
                           user_search_form=UserSearchForm(),
                           users = users,
                          )


def get_updated_chats(user):
    available_chats = user.get_available_chats_query().all()
    chats = []
    messages = []
    for chat in available_chats:
        unread_messages_query = user.get_unread_messages_query(chat)
        count = unread_messages_query.count()
        if count:
            chats.append({'chat_id': str(chat.id),
                          'unread_messages_count': count,
                          'chat_name': chat.get_name(user)})
            current_chat_id = session.get('current_chat_id')
            if current_chat_id == chat.id:
                messages = (Message
                            .get_messages_list(unread_messages_query))
    if chats:
        data = {'chats': chats,
                'current_chat_messages': messages,
                'current_username': user.username}
        return data


def send_update(data, sid):
    socket_io.emit('chat_updated', data, room=sid)


@main.before_app_request
def before_request():
    if current_user.is_authenticated and current_user.confirmed:
        current_user.last_seen = datetime.now(tz=timezone.utc)

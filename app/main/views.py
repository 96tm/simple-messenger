from flask import current_app
from flask import render_template, session
from flask_login import current_user, login_required
from datetime import datetime, timezone
import json

from . import main
from .ajax import add_contacts_and_chats, check_new_messages, choose_chat
from .ajax import load_chats, load_users, remove_chat, search_chats
from .ajax import search_users, send_message
from .forms import ChatSearchForm, MessageForm, UserSearchForm
from .. import database
from ..models import Chat, User


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
    for chat in chats:
        recipient = chat.users.filter(User.id != current_user.id).first()
        name = chat.name or recipient.username
        chat_list.append({'name': name, 'chat_id': chat.id})
    messages = None
    current_chat_id = None
    current_chat_name = None
    if session.get('current_chat_id'):
        current_chat_id = session.get('current_chat_id')
    if current_chat_id and Chat.query.get(current_chat_id):
        chat = Chat.query.get_or_404(current_chat_id)
        messages = current.get_messages(chat)
        current_chat_name = chat.get_name(current)
    return render_template('index.html',
                           chats = chat_list,
                           users = users,
                           current_chat_id=current_chat_id,
                           current_chat_name=current_chat_name,
                           message_form = MessageForm(),
                           user_search_form=UserSearchForm(),
                           chat_search_form=ChatSearchForm())


@main.before_app_request
def before_request():
    if current_user.is_authenticated and current_user.confirmed:
        current_user.last_seen = datetime.now(tz=timezone.utc)

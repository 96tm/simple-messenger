from . import api, errors
from .authentication import auth
from .. import database
from ..models import Message, User

from flask import abort, current_app, g, jsonify, request, url_for


@api.route('/chats/<int:chat_id>/messages')
@auth.login_required
def get_messages(chat_id):
    page = request.args.get('page', 1, type=int)
    prev_page = None
    next_page = None
    chat = (g.current_user
            .get_available_chats_query()
            .filter_by(id=chat_id).first())
    if not chat:
        abort(404)
    pagination = (chat
                  .messages
                  .paginate(page, 
                            current_app.config['MESSAGES_PER_PAGE'],
                            error_out=False))
    if pagination.has_prev:
        prev_page = url_for('api.get_messages', 
                            chat_id=chat_id, 
                            page=page-1, 
                            _external=True)
    if pagination.has_next:
        next_page = url_for('api.get_messages', 
                            chat_id=chat_id, 
                            page=page+1, 
                            _external=True)
    messages = [message.to_json(g.current_user) 
                for message 
                in pagination.items]
    return jsonify({'messages': messages,
                    'previous': prev_page,
                    'next': next_page,
                    'count': pagination.total})

@api.route('/chats/<int:chat_id>/messages/<int:message_id>')
@auth.login_required
def get_message(chat_id, message_id):
    chat = (g.current_user
            .get_available_chats_query()
            .filter_by(id=chat_id).first())
    if not chat:
        abort(404)
    message = chat.messages.filter_by(id=message_id).first()
    if not message:
        abort(404)
    return jsonify(message.to_json(g.current_user))


@api.route('/chats/<int:chat_id>/messages/', methods=['POST'])
@auth.login_required
def new_message(chat_id):
    chat = (g.current_user
            .get_available_chats_query()
            .filter_by(id=chat_id).first())
    if not chat:
        abort(404)
    recipient = None
    if not chat.is_group_chat:
        recipient = (chat
                    .users
                    .filter(User.id != g.current_user.id)
                    .first())
    else:
        abort(404)
    message = Message.from_json(request.json)
    if not message:
        return errors.generate_error(errors.CONFLICT,
                                     'cannot process client data')
    message.sender = g.current_user
    message.chat = chat
    message.recipient = recipient
    database.session.add(message)
    database.session.commit()
    return (jsonify(message.to_json(g.current_user)), 
            201,
            {'Location': url_for('api.get_message', 
                                 chat_id=chat.id, 
                                 message_id=message.id,
                                 _external=True)})

from . import api
from .authentication import auth

from flask import abort, current_app, g, jsonify, request, url_for


@api.route('/chats')
@auth.login_required
def get_chats():
    page = request.args.get('page', 1, type=int)
    prev_page = None
    next_page = None
    pagination = (g.current_user
                  .get_available_chats_query()
                  .paginate(page, 
                            current_app.config['CHATS_PER_PAGE'], 
                            error_out=False))
    if pagination.has_prev:
        prev_page = url_for('api.get_chats', page=page-1, _external=True)
    if pagination.has_next:
        prev_page = url_for('api.get_chats', page=page+1, _external=True)
    chats = [chat.to_json(g.current_user) for chat in pagination.items]
    return jsonify({'chats': chats,
                    'previous': prev_page,
                    'next': next_page,
                    'count': pagination.total})


@api.route('/chats/<int:chat_id>')
@auth.login_required
def get_chat(chat_id):
    chat = (g.current_user
            .get_available_chats_query()
            .filter_by(id=chat_id).first())
    if not chat:
        abort(404)
    return jsonify(chat.to_json(g.current_user))
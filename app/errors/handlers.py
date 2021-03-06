from flask import render_template, jsonify, request
from . import errors_blueprint


@errors_blueprint.app_errorhandler(404)
def page_not_found(e):
    if (request.accept_mimetypes.accept_json 
        and not request.accept_mimetypes.accept_html):
            response = jsonify({'error': 'not found'})
            response.status_code = 404
            return response
    return render_template('errors/404.html'), 404


@errors_blueprint.app_errorhandler(500)
def internal_server_error(e):
    if (request.accept_mimetypes.accept_json 
        and not request.accept_mimetypes.accept_html):
            response = jsonify({'error': 'server error'})
            response.status_code = 500
            return response
    return render_template('errors/500.html'), 500

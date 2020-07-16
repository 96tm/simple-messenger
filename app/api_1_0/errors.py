from flask import jsonify
from collections import namedtuple
from . import api
from ..exceptions import ValidationError


Error = namedtuple('error', ('name', 'status_code'))


BAD_REQUEST = Error('bad request', 400)
FORBIDDEN = Error('forbidden', 403)
UNAUTHORIZED = Error('unauthorized', 401)
METHOD_NOT_ALLOWED = Error('method not allowed', 405)
CONFLICT = Error('conflict', 409)


def generate_error(error, message=''):
    response = jsonify({'error': error.name, 'message': message,
                        'status': error.status_code})
    response.status_code = error.status_code
    return response


@api.errorhandler(ValidationError)
def validation_error(e):
    return generate_error(BAD_REQUEST, e.args[0])

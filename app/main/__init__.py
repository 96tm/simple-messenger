from flask import Blueprint
from ..models import Permission


main = Blueprint('main', __name__)


@main.app_context_processor
def inject_permissions():
    return {'Permission': Permission}


from . import routes
# from app.errors import handlers 

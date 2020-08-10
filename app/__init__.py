from celery import Celery
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_session import Session

from config import Config

import os


celery = Celery(__name__)
database = SQLAlchemy()
login_manager = LoginManager()
flask_session = Session()
mail = Mail()
migrate = Migrate()
socket_io = SocketIO(manage_session=False, async_mode='gevent')
wsgi_application = Flask(__name__)


def set_celery(app):
    celery.conf.update(app.config)
    celery.conf.name = app.name
    celery.conf.broker_url = app.config['CELERY_BROKER_URL']
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


def create_app():
    wsgi_application.config.from_object(Config)
    set_celery(wsgi_application)
    database.init_app(wsgi_application)
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'
    login_manager.init_app(wsgi_application)
    mail.init_app(wsgi_application)
    migrate.init_app(wsgi_application, database)
    socket_io.init_app(wsgi_application)
    flask_session.init_app(wsgi_application)

    from .auth import auth as auth_blueprint
    from .auth.before_auth_request import before_auth_request
    auth_blueprint.before_request(before_auth_request)
    wsgi_application.register_blueprint(auth_blueprint, 
                                        url_prefix='/auth')

    from .api_1_0 import api as api_blueprint
    wsgi_application.register_blueprint(api_blueprint,
                                        url_prefix='/api/v1.0')

    from .errors import errors_blueprint
    wsgi_application.register_blueprint(errors_blueprint)

    from .main import main as main_blueprint
    wsgi_application.register_blueprint(main_blueprint)

    return wsgi_application


from app import models

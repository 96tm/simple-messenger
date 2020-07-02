from flask import Flask, Blueprint
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from config import config


database = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
moment = Moment()
bootstrap = Bootstrap()


def create_app(config_name):
    wsgi_application = Flask(__name__)
    wsgi_application.config.from_object(config[config_name])
    bootstrap.init_app(wsgi_application)
    database.init_app(wsgi_application)
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'
    login_manager.init_app(wsgi_application)
    mail.init_app(wsgi_application)
    moment.init_app(wsgi_application)

    from .main import main as main_blueprint
    wsgi_application.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    wsgi_application.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api_1_0 import api as api_blueprint
    wsgi_application.register_blueprint(api_blueprint, url_prefix='/api/v1.0')

    return wsgi_application

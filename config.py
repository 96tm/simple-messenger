import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change_debug_secret_key!')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAIL_SUBJECT_PREFIX = '[SimpleMessenger]'
    MAIL_SENDER = os.environ.get('MAIL_SENDER', 'Admin <use@some.mail')
    ADMIN = os.environ.get('SIMPLE_MESSENGER_ADMIN', 'Admin')
    ADMIN_MAIL = 'admin@admin.admin'
    MAX_STRING_LENGTH = 64
    USERS_PER_PAGE = 10
    CHATS_PER_PAGE = 10
    MESSAGES_PER_PAGE = 10

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    name = 'development'
    DEBUG = True
    MAIL_SERVER = 'smtp.mail.ru'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI',
                                             ('sqlite:///' 
                                              + os.path.join(basedir, 
                                                             'app.db')))


class TestingConfig(Config):
    name = 'testing'
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class ProductionConfig(Config):
    name = 'production'
    DEBUG = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI',
                                             ('sqlite:///' 
                                              + os.path.join(basedir, 
                                                             'app.db')))

config = {'development': DevelopmentConfig,
          'testing':     TestingConfig,
          'production':  ProductionConfig,

          'default':     DevelopmentConfig}

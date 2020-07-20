import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change_debug_secret_key!')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')
    
    MAIL_SUBJECT_PREFIX = os.environ.get('MAIL_SUBJECT_PREFIX',
                                         '[SimpleMessenger]')
    MAIL_SENDER = os.environ.get('MAIL_SENDER', 'Admin <use@some.mail')
    MAIL_USERNAME = MAIL_SENDER[:MAIL_SENDER.rfind('@')]
    MAIL_PORT = os.environ.get('MAIL_PORT', 587)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMIN = os.environ.get('SIMPLE_MESSENGER_ADMIN', 'Admin')
    ADMIN_MAIL = os.environ.get('ADMIN_MAIL', 'admin@admin.admin')
    MAX_STRING_LENGTH = 64
    USERS_PER_PAGE = 10
    CHATS_PER_PAGE = 10
    MESSAGES_PER_PAGE = 10
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI',
                                             ('sqlite:///' 
                                              + os.path.join(basedir,
                                              		      'database',
                                                             'app.db')))

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    name = 'development'
    DEBUG = True
    MAIL_USE_TLS = True



class TestingConfig(Config):
    name = 'testing'
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class ProductionConfig(Config):
    name = 'production'
    DEBUG = False
    MAIL_USE_TLS = True


config = {'development': DevelopmentConfig,
          'testing':     TestingConfig,
          'production':  ProductionConfig,

          'default':     DevelopmentConfig}

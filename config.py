import os
basedir = os.path.abspath(os.path.dirname(__file__))

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

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.mail.ru'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = ('postgresql://' 
                                         + os.environ['FLASK_DB_USER']
                                         + ':' 
                                         + os.environ['FLASK_DB_PASS']
                                         + '@'
                                         + os.environ['FLASK_DB_HOSTNAME'] + '/'
                                         + 'simple_messenger_db')

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    pass

config = {'development': DevelopmentConfig,
          'testing':     TestingConfig,
          'production':  ProductionConfig,

          'default':     DevelopmentConfig}

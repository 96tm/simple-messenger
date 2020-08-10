import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
envdir = os.path.join(basedir, '.env')
load_dotenv(envdir)


class Config:
    name = 'default'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change_debug_secret_key!')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')
    
    MAIL_SUBJECT_PREFIX = os.environ.get('MAIL_SUBJECT_PREFIX',
                                         '[Simple Messenger]')
    MAIL_SENDER = os.environ.get('MAIL_SENDER', 'Admin <use@some.mail')
    MAIL_USERNAME = MAIL_SENDER[:MAIL_SENDER.rfind('@')]
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USE_TLS = int(os.environ.get('MAIL_USE_TLS', True))
    ADMIN = os.environ.get('SIMPLE_MESSENGER_ADMIN', 'Admin')
    ADMIN_MAIL = os.environ.get('ADMIN_MAIL', 'admin@admin.admin')
    MAX_STRING_LENGTH = 64
    USERS_PER_PAGE = 10
    CHATS_PER_PAGE = 10
    MESSAGES_PER_PAGE = 10

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI',
                                             'sqlite:///memory')
    DEBUG = int(os.environ.get('DEBUG', False))
    TESTING = int(os.environ.get('TESTING', False))
    WTF_CSRF_ENABLED = int(os.environ.get('WTF_CSRF_ENABLED', True))
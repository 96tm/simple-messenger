from . import login_manager
from . import database
from datetime import datetime, timezone
from itsdangerous import BadHeader
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.ext.associationproxy import association_proxy
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Role(database.Model):
    __tablename__ = 'roles'
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(64), unique=True)

    users = database.relationship('User', backref='role')

    def __repr__(self):
        return f'Role(id={self.id}, name={self.name}'


class User(UserMixin, database.Model):
    __tablename__ = 'users'
    id = database.Column(database.Integer, primary_key=True)
    confirmed = database.Column(database.Boolean, default=False)
    role_id = database.Column(database.Integer, database.ForeignKey('roles.id'))
    registration_date = database.Column(database.DateTime, nullable=False,
                                        default=datetime.now(timezone.utc))
    username = database.Column(database.String(64), 
                               unique=True,
                               index=True,
                               nullable=False)
    email = database.Column(database.String(64),
                            unique=True,
                            index=True,
                            nullable=False)
    password_hash = database.Column(database.String(128), nullable=False)

    users = association_proxy('user_relations', 'user')
    contacts = association_proxy('contact_relations', 'contact')

    messages_from = database.relationship('Message', primaryjoin='User.id==Message.sender_id')
    messages_to = database.relationship('Message', primaryjoin='User.id==Message.recipient_id')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return (f'User(id={self.id}, username={self.username}, '
                + f'registration_date={self.registration_date})')
    
    def add_contact(self, contact, contact_group=None):
        relation = UserContactsAssociation(user=self, contact=contact)
        database.session.add(self)
    
    def generate_confirmation_token(self, expiration=3600):
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'confirm': self.id})
    
    def confirm(self, token):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except BadHeader:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        database.session.add(self)
        return True


class Message(database.Model):
    __tablename__ = 'messages'
    id = database.Column(database.Integer, primary_key = True)
    text = database.Column(database.Text)
    message_date = database.Column(database.DateTime,
                                   nullable=False,
                                   default=datetime.now(timezone.utc))
    sender_id = database.Column(database.Integer, 
                                database.ForeignKey('users.id'),
                                nullable=False)
    recipient_id = database.Column(database.Integer,
                                   database.ForeignKey('users.id'),
                                   nullable=False)

    sender = database.relationship('User', foreign_keys=[sender_id])
    recipient = database.relationship('User', foreign_keys=[recipient_id])

    def __repr__(self):
        return (f'Message(id={self.id}, text={self.text}, sender={self.sender.username} '
                + f'recipient={self.recipient.username}, message_date={self.message_date}')


class UserContactsAssociation(database.Model):
    __tablename__ = 'user_contacts_association'
    user_id = database.Column(database.Integer,
                              database.ForeignKey('users.id'),
                              primary_key=True)
    contact_id = database.Column(database.Integer,
                                 database.ForeignKey('users.id'),
                                 primary_key=True)
    contact_group = database.Column(database.String(16), nullable=True)

    user = database.relationship('User',
                                   primaryjoin=(user_id == User.id),
                                   backref='contact_relations')
    contact = database.relationship('User',
                                 primaryjoin=(contact_id == User.id),
                                 backref='user_relations')

from . import login_manager
from . import database
from datetime import datetime, timezone
from itsdangerous import BadHeader
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.ext.associationproxy import association_proxy
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Role(database.Model):
    __tablename__ = 'roles'
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(64), unique=True)
    is_default = database.Column(database.Boolean, default=False, index=True, nullable=False)
    permissions = database.Column(database.Integer)

    users = database.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'Role(id={self.id}, name={self.name}'

    # change admin permissions to the disjunction of all the available
    # permissions in future
    
    @staticmethod
    def insert_roles(roles=None):
        if roles is None:
            roles = {'Admin': {'permissions': 0xff, 
                               'is_default': False},
                     'User': {'permissions': 0,
                              'is_default': True}
            }
        for role in roles:
            new_role = Role.query.filter_by(name=role).first()
            if new_role is None:
                new_role = Role(name=role)
            new_role.permissions = roles[role]['permissions']
            new_role.is_default = roles[role]['is_default']
            database.session.add(new_role)
        database.session.commit()


class User(UserMixin, database.Model):
    __tablename__ = 'users'
    id = database.Column(database.Integer, primary_key=True)
    confirmed = database.Column(database.Boolean, default=False)
    last_seen = database.Column(database.DateTime, nullable=True)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN_MAIL']:
                self.role = Role.query.filter_by(permissions = 0xff).first()
            else:
                self.role = Role.query.filter_by(is_default=True).first()
            
    def __repr__(self):
        return (f'User(id={self.id}, username={self.username}, '
                + f'registration_date={self.registration_date}, '
                + f'confirmed={self.confirmed})')
    
    @property
    def is_admin(self):
        return self.role and self.has_permission(Permission.ADMINISTRATION)

    def has_permission(self, permission):
        return (self.role is not None
                and (self.role.permissions & permission == permission))
    

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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


class AnonymousUser(AnonymousUserMixin):
    def has_permission(self, permission):
        return False
    
    @property
    def is_admin(self):
        return False


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


class Permission:
    ADMINISTRATION = 1

login_manager.anonymous_user = AnonymousUser

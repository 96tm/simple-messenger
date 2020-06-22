from . import login_manager
from . import database
from datetime import datetime, timezone
from itsdangerous import BadHeader, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy import and_, not_, or_
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def add_test_data():
    database.create_all()
    bob = User(username='bob', email='bob@bob.bob', 
               password='bob', confirmed=True)
    arthur = User(username='arthur', email='arthur@arthur.arthur',
                  password='arthur', confirmed=True)
    morgana = User(username='morgana', email='morgana@morgana.morgana',
                   password='morgana', confirmed=True)
    clair = User(username='clair', email='clair@clair.clair',
                 password='clair', confirmed=True)
    merlin = User(username='merlin', email='merlin@merlin.merlin',
                  password='merlin', confirmed=True)
    ophelia = User(username='ophelia', email='ophelia@ophelia.ophelia',
                   password='ophelia', confirmed=True)
    database.session.add_all([bob, arthur, morgana, clair, merlin, ophelia])
    chat0 = Chat()
    chat0.add_users([bob, arthur])
    chat1 = Chat()
    chat1.add_users([bob, clair])
    chat2 = Chat()
    chat2.add_users([arthur, morgana])
    database.session.add_all([chat0, chat1, chat2])
    database.session.commit()



UserChatTable = database.Table(
    'user_chat_link',
    database.Column('user_id',
                    database.Integer,
                    database.ForeignKey('users.id',
                                        ondelete="CASCADE"),
                    primary_key=True),
    database.Column('chat_id',
                    database.Integer,
                    database.ForeignKey('chats.id',
                                        ondelete="CASCADE"),
                    primary_key=True)
)


class RemovedChat(database.Model):
    __tablename__ = 'removed_chats'
    user_id = database.Column(database.Integer, 
                              database.ForeignKey('users.id',
                                                  ondelete="CASCADE"),
                              primary_key=True)
    chat_id = database.Column(database.Integer,
                              database.ForeignKey('chats.id',
                                                  ondelete="CASCADE"),
                              primary_key=True)


class Role(database.Model):
    __tablename__ = 'roles'
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(64), unique=True)
    is_default = database.Column(database.Boolean, 
                                 default=False, 
                                 index=True, 
                                 nullable=False)
    permissions = database.Column(database.Integer)

    users = database.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'Role(id={self.id}, name={self.name}'

    # TODO
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


class Contact(database.Model):
    __tablename__ = 'contacts'
    user_id = database.Column(database.Integer,
                              database.ForeignKey('users.id'),
                              primary_key=True)
    contact_id = database.Column(database.Integer,
                                 database.ForeignKey('users.id'),
                                 primary_key=True)
    contact_group = database.Column(database.String(16), nullable=True)

    date_created = database.Column(database.DateTime,
                                   default=datetime.now(tz=timezone.utc))


class Chat(database.Model):
    __tablename__ = 'chats'

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(64))
    is_group_chat = database.Column(database.Boolean, default=False)
    date_created = database.Column(database.DateTime, 
                                   default=datetime.now(tz=timezone.utc))
    date_modified = database.Column(database.DateTime,
                                    default=datetime.now(tz=timezone.utc))
    
    removed_users = database.relationship('RemovedChat',
                                          backref='chat',
                                          lazy='dynamic',
                                          cascade='all, delete-orphan')

    def add_users(self, users):
        for user in users:
            if not user in self.users.all():
                self.users.append(user)
        database.session.commit()
    
    def remove_users(self, users):
        for user in users:
            self.users.remove(user)
        database.session.commit()
    
    @staticmethod
    def get_chat(user1, user2):
        '''
        Return chat between user1 and user2
        '''
        return (Chat
                .query
                .filter(and_(Chat.users.contains(user1),
                             Chat.users.contains(user2),
                             not_(Chat.is_group_chat)))
                .first())

    @staticmethod
    def get_removed_query(user, chat_query=None):
        '''
        Return RemovedChat instances for user
        (based on chat query, if given)
        '''
        if chat_query:
            return (RemovedChat
                    .query
                    .filter(and_(RemovedChat.user == user,
                                 RemovedChat
                                 .chat_id
                                 .in_([chat.id
                                       for chat
                                       in chat_query.all()]
                                     )
                                )
                            )
                    )
        else:
            return (RemovedChat
                    .query
                    .filter(RemovedChat.user==user))

    @staticmethod
    def get_chat_query(user, user_ids):
        '''
        Return chats of user with users identified by user_ids
        '''
        return (Chat
                .query
                .filter(Chat.users.contains(user))
                .join(UserChatTable, 
                    and_(UserChatTable.c.chat_id == Chat.id,
                         UserChatTable.c.user_id.in_(user_ids)
                        )
                    )
                )
    
    @classmethod
    def get_removed_chats(cls, user, user_ids):
        '''
        Return list of user's chats
        from users having user_ids marked as removed
        and delete records about the chats from RemovedChat
        '''
        chat_query = cls.get_chat_query(user, user_ids)
        removed_chat_query = cls.get_removed_query(user, chat_query)
        chats = (chat_query
                .join(removed_chat_query.subquery(),
                      Chat
                      .id
                      .in_([removed.chat_id 
                            for removed
                            in removed_chat_query]
                          )
                     )
                .all()
                )
        removed_chat_query.delete(synchronize_session='fetch')
        return chats
  
    @staticmethod
    def mark_chats_as_removed(user, chats):
        '''
        Add a record to RemovedChat for user and each chat in chats sequence
        '''
        for chat in chats:
            removed_chat = RemovedChat()
            removed_chat.user = user
            removed_chat.chat = chat
            database.session.add(removed_chat)
        database.session.commit()


class User(UserMixin, database.Model):
    __tablename__ = 'users'
    id = database.Column(database.Integer, primary_key=True)
    confirmed = database.Column(database.Boolean, default=False)
    last_seen = database.Column(database.DateTime, nullable=True)
    role_id = database.Column(database.Integer, 
                              database.ForeignKey('roles.id'))
    date_created = database.Column(database.DateTime, nullable=False,
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

    contacts = database.relationship('Contact',
                                     foreign_keys=[Contact.user_id],
                                     backref=database.backref('user', 
                                                              lazy='joined'),
                                     lazy='dynamic',
                                     cascade='all, delete-orphan')
    contacted = database.relationship('Contact', 
                                      foreign_keys=[Contact.contact_id],
                                      backref=database.backref('contact', 
                                                               lazy='joined'),
                                      lazy='dynamic',
                                      cascade='all, delete-orphan')

    messages_from = (database
                     .relationship('Message', 
                                   primaryjoin='User.id==Message.sender_id'))
    messages_to = (database
                   .relationship('Message',
                                 primaryjoin='User.id==Message.recipient_id'))
    chats = database.relationship('Chat',
                                  secondary=UserChatTable,
                                  backref=database.backref('users', lazy='dynamic'))

    removed_chats = database.relationship('RemovedChat',
                                          backref='user',
                                          lazy='dynamic',
                                          cascade='all, delete-orphan')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN_MAIL']:
                self.role = Role.query.filter_by(permissions = 0xff).first()
            else:
                self.role = Role.query.filter_by(is_default=True).first()
            
    def __repr__(self):
        return (f'User(id={self.id}, username={self.username}, '
                + f'date_created={self.date_created}, '
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
    
    def has_contact(self, user):
        return bool(self.contacts.filter_by(contact_id=user.id).first())
    
    def is_contacted_by(self, user):
        return bool(self.contacted.filter_by(user_id=user.id).first())
    
    def add_contacts(self, users, contact_group=None):
        for user in users:
            if not self.has_contact(user):
                relation = Contact(user=self, 
                                   contact=user,
                                   contact_group=contact_group)
                database.session.add(relation)

    def delete_contacts(self, users):
        for user in users:
            if self.has_contact(user):
                relation = self.contacts.filter_by(contact_id=user.id).first()
                database.session.delete(relation)
    
    def generate_confirmation_token(self, expiration=3600):
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'confirm': self.id})
    
    def confirm(self, token):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except (BadHeader, SignatureExpired):
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        database.session.add(self)
        return True
    
    def get_other_users(self):
        '''
        Return list of users not including user
        '''
        return (User
                .query
                .filter(User.id != self.id)
                .order_by(User.username)
                .all())
    
    def get_available_chats(self):
        '''
        Return query of user's chats not marked as removed
        '''
        removed_chats = Chat.get_removed_query(self)
        return (Chat
                .query
                .filter(Chat.users.contains(self))
                .filter(not_(Chat
                            .id
                            .in_(removed_chats
                                .with_entities(RemovedChat.chat_id))))
                .order_by(Chat.date_modified.desc()).all())


class Message(database.Model):
    __tablename__ = 'messages'

    id = database.Column(database.Integer, primary_key = True)
    was_read = database.Column(database.Boolean,
                               default=False)
    text = database.Column(database.Text)
    date_created = database.Column(database.DateTime,
                                   nullable=False,
                                   default=datetime.now(timezone.utc))
    sender_id = database.Column(database.Integer, 
                                database.ForeignKey('users.id'),
                                nullable=False)
    recipient_id = database.Column(database.Integer,
                                   database.ForeignKey('users.id'),
                                   nullable=False)
    chat_id = database.Column(database.Integer,
                              database.ForeignKey('chats.id'),
                              nullable=False)

    sender = database.relationship('User', foreign_keys=[sender_id])
    recipient = database.relationship('User', foreign_keys=[recipient_id])
    chat = database.relationship('Chat',
                                 backref=database.backref('messages',
                                                          lazy='dynamic'),
                                 foreign_keys=[chat_id])

    def __repr__(self):
        return (f'Message(id={self.id}, text={self.text}, ' 
                + f'sender={self.sender.username}, '
                + f'recipient={self.recipient.username}, ' 
                + f'date_created={self.date_created})')
    
    @staticmethod
    def flush_messages(message_query):
        '''
        Set 'was_read' column to True for all messages from message_query
        '''
        message_query.update({'was_read': True}, synchronize_session=False)
        database.session.commit()


class AnonymousUser(AnonymousUserMixin):
    def has_permission(self, permission):
        return False
    
    @property
    def is_admin(self):
        return False


class Permission:
    ADMINISTRATION = 1


login_manager.anonymous_user = AnonymousUser

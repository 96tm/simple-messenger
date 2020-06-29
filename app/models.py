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
    """
    Set up current user
    """
    return User.query.get(int(user_id))


def format_date(date):
    """
    Return string representation of given date

    :param date: DateTime instance
    :returns: string
    """
    date_format = '%A, %B %d %Y %H:%M'
    return date.strftime(date_format)


def add_test_data():
    """
    Load data to database
    for testing purposes.
    """
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


# association table for many-to-many relationship
# between User model and Chat model
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
    """
    Association table
    to keep track of which users
    mark which chats as removed.
    """
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
    """
    Represents user role for managing
    permission.

    Static methods defined here:

    insert_roles(roles=None)
    """
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
        """
        Insert given roles to database.
        Insert a default set of roles if
        called with no parameters.

        :param roles: dictionary of roles
                      in the form 
                      {'role_name': {'permissions': int, 
                                     'is_default': bool}}
        """
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
    """
    Association table
    representing many-to-many relationship
    among User model instances.
    """
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
    """
    Represents a chat,
    which is defined as a collection of
    users and messages.
    

    Methods defined here:

    get_name()

    add_users(users)

    delete_users(users)

    get_chat(user_1, user_2)


    Static methods defined here:

    search_chats_query(chat_name, user)

    get_removed_query(user, chat_query=None)

    get_chat_query(user, user_ids)

    mark_chats_as_removed(user, chats)


    Class methods defined here:

    get_removed_chats(user, user_ids)
    """
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

    def get_name(self, user):
        """
        Return current chat's 'name' if present,
        otherwise return 'username'
        of first user of current chat's users attribute
        which is not equal to given user's username

        :param user: User model instance
        :returns: string
        """
        if self.name:
            return self.name
        recipient = (self
                     .users
                     .filter(User.username != user.username)
                     .first())
        return recipient.username

    def add_users(self, users):
        """
        Add given users to current chat.

        :param users: sequence of User model instances
        """
        for user in users:
            if not user in self.users.all():
                self.users.append(user)
        database.session.commit()
    
    def remove_users(self, users):
        """
        Delete given users from current chat.

        :param users: sequence of User model instances
        """
        for user in users:
            self.users.remove(user)
        database.session.commit()
    
    @staticmethod
    def search_chats_query(chat_name, user):
        """
        Return query of chats
        where each chat either:
        - contains given chat_name in 'name' column;
        - has only two users ('is_group_chat' is False and 'name' is None),
          and the user with 'username' != given user's 'username'
          contains given chat_name in 'username'.

        :param chat_name: string to search for
        :param user: user whose 'username' is excluded from search,
                     i.e. if 
                     chat.users == [User(username='bob'), 
                                    User(username='arthur')] 
                     and chat.name == None, 
                     then search_chats('bob', User(username='bob'))
        :returns: Chat model query
        """
        subquery_current = (User
                            .query
                            .filter(User
                                    .username == user.username)
                            .subquery())
        subquery_pattern = (User
                            .query
                            .filter(User.username != user.username,
                                    User
                                    .username
                                    .like('%' + chat_name + '%'))
                            .subquery())
        subquery_current_chats = (database
                                 .session
                                 .query(UserChatTable.c.chat_id)
                                 .join(subquery_current,
                                       UserChatTable
                                       .c
                                       .user_id == subquery_current.c.id)
                                 .subquery())
        subquery_pattern_chats = (database
                                  .session
                                  .query(UserChatTable.c.chat_id)
                                  .join(subquery_pattern,
                                        UserChatTable
                                        .c
                                        .user_id == subquery_pattern.c.id)
                                  .subquery())
        chats = (database
                 .session
                 .query(Chat)
                 .join(subquery_current_chats,
                       Chat.id == subquery_current_chats.c.chat_id)
                 .join(subquery_pattern_chats,
                       subquery_current_chats
                       .c
                       .chat_id == subquery_pattern_chats.c.chat_id))

        return (database
                .session
                .query(Chat)
                .filter(Chat.users.contains(user), Chat.name.like('%' + chat_name + '%'))
                .union(chats))
    
    @staticmethod
    def get_chat(user_1, user_2):
        """
        Return chat between user_1 and user_2

        :param user_1: User model instance
        :param user_2: User model instance
        :returns: Chat model instance
        """
        return (Chat
                .query
                .filter(and_(Chat.users.contains(user_1),
                             Chat.users.contains(user_2),
                             not_(Chat.is_group_chat)))
                .first())

    @staticmethod
    def get_removed_query(user, chat_query=None):
        """
        Return RemovedChat query for user
        (based on chat query, if given).

        :param user: User model instance
        :param chat_query: Chat model query
        :returns: RemovedChat model query
        """
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
        """
        Return query of chats 
        of given user with users 
        identified by given user_ids
        
        :param user: User model instance
        :param user_ids: sequence of integers
        :returns: Chat model query
        """
        return (Chat
                .query
                .filter(Chat.users.contains(user))
                .join(UserChatTable, 
                    and_(UserChatTable.c.chat_id == Chat.id,
                         UserChatTable.c.user_id.in_(user_ids)
                        )
                    )
                )

    @staticmethod
    def mark_chats_as_removed(user, chats):
        """
        Add RemovedChat record
        for each chat in given chats for given user.
        
        :param user: User model instance
        :param chats: sequence of Chat model instances
        """
        for chat in chats:
            removed_chat = RemovedChat()
            removed_chat.user = user
            removed_chat.chat = chat
            database.session.add(removed_chat)
        database.session.commit()
    
    @classmethod
    def get_removed_chats(cls, user, user_ids):
        """
        Return list of chats of given user
        with users having
        given user_ids
        which are marked as removed by current user.
        Delete records about the chats from RemovedChat.
        
        :param user: User model instance
        :param user_ids: sequence of integers
        :returns: list of Chat model instances
        """
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


class User(UserMixin, database.Model):
    """
    User model. Implements UserMixin, 
    used as a default authentication model by Flask-Login.

    Methods defined here:

    has_permission(permission)

    verify_password(password)
    
    generate_confirmation_token(expiration=3600)
    
    confirm(token)
    
    has_contact(user)
    
    is_contacted_by(user)
    
    add_contacts(users, contact_group=None)
    
    delete_contacts(users)
    
    get_other_users_query()
    
    get_available_chats_query()
    
    get_messages(chat)
    
    get_unread_messages(chat)
    
    search_users_query(username, users_query)
    """
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
        """
        Check if current user has admin permissions.

        :returns: True if current user has admin permission,
                  False otherwise
        """
        return self.role and self.has_permission(Permission.ADMINISTRATION)
   
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        """
        Assign given password to current user.

        :param password: string
        """
        self.password_hash = generate_password_hash(password)
    
    def has_permission(self, permission):
        """
        Check if current user has given permission

        :param permission: integer representing permission
        :returns: True if current user has a role
                  and the role has permission,
                  False otherwise

        """
        return (self.role is not None
                and (self.role.permissions & permission == permission))
    
    
    def verify_password(self, password):
        """
        Check if given password matches current user's password.

        :param password: string
        :returns: True if password matches current user's password, 
                  False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def generate_confirmation_token(self, expiration=3600):
        """
        Return a confirmation token for current user.

        :param expiration: Time in seconds after which token expires
        :returns: TimedJSONWebSignature
        """
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'confirm': self.id})
    
    def confirm(self, token):
        """
        Check that given token belongs to current user
        and set current user's 'confirmed' column to True
        if it does.

        :param token: TimedJSONWebSignature instance
        :returns: True if given token belongs to current user,
                  False otherwise
        """
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

    def has_contact(self, user):
        """
        Check if current user has given user as a contact.

        :param user: User model instance
        :returns: True if current user has user as a contact,
                  False otherwise
        """
        return bool(self.contacts.filter_by(contact_id=user.id).first())
    
    def is_contacted_by(self, user):
        """
        Check if given user has current user as a contact

        :param user: User model instance
        :returns: True if user has current user as a contact,
                  False otherwise
        """
        return bool(self.contacted.filter_by(user_id=user.id).first())
    
    def add_contacts(self, users, contact_group=None):
        """
        Add users to contacts of current user.

        :param users: list of User model instances
        :param contact_group: name of contact group
        """
        for user in users:
            if not self.has_contact(user):
                relation = Contact(user=self, 
                                   contact=user,
                                   contact_group=contact_group)
                database.session.add(relation)

    def delete_contacts(self, users):
        """
        Delete users from contacts of current user.

        :param users: sequence of User model instances
        """
        for user in users:
            if self.has_contact(user):
                relation = self.contacts.filter_by(contact_id=user.id).first()
                database.session.delete(relation)
    
    def get_other_users_query(self):
        """
        Return query of users not including user
        ordered by column 'username' in ascending order.

        :returns: User model query
        """
        return (User
                .query
                .filter(User.id != self.id)
                .order_by(User.username))
    
    def get_available_chats_query(self):
        """
        Return query of current user's chats 
        not marked as removed.

        :returns: User model query
        """
        removed_chats = Chat.get_removed_query(self)
        return (Chat
                .query
                .filter(Chat.users.contains(self))
                .filter(not_(Chat
                            .id
                            .in_(removed_chats
                                .with_entities(RemovedChat.chat_id))))
                .order_by(Chat.date_modified.desc()))

    def get_messages(self, chat):
        """
        Return a list of dictionaries with keys
        'text', 'date_created', 'sender_username', 'recipient_username'
        for messages of given chat and set column 'was_read' to True
        for messages received by user and not yet read.

        :param chat: Chat model instance
        :returns: list of dictionaries
        """
        query_to_update = (chat
                           .messages
                           .filter(and_(Message.sender != self,
                                        not_(Message.was_read))))

        messages = chat.messages.order_by(Message.date_created).all()

        message_dict_list = []
        for message in messages:
            sender = message.sender
            recipient = message.recipient
            sender_name = sender.username if sender else None
            recipient_name = recipient.username if recipient else None
            message_dict = {'text': message.text,
                            'date_created': format_date(message.date_created),
                            'sender_username': sender_name,
                            'recipient_username': recipient_name}
            message_dict_list.append(message_dict)
        Message.flush_messages(query_to_update)
        return message_dict_list

    def get_unread_messages(self, chat):
        """
        Return a list of dictionaries with keys 
        'text', 'sender_username', 'date_created'
        for unread messages from given chat to curent user.

        :param chat: Chat model instance
        :returns: list of dictionaries
        """
        query = (chat
                 .messages
                 .filter(and_(Message.sender != self,
                              not_(Message.was_read))))
        messages = query.order_by(Message.date_created).all()
        message_dict_list = []
        for message in messages:
            sender = message.sender
            sender_username = sender.username if sender else None
            date_created = format_date(message.date_created)
            message_dict = {'text': message.text,
                            'sender_username': sender_username,
                            'date_created': date_created}
            message_dict_list.append(message_dict)
        Message.flush_messages(query)
        return message_dict_list

    def search_users_query(self, username, users_query):
        """
        Return query of users from given users_query
        containing string in 'username'
        except current user
        in ascending lexicographical order by 'username'.

        :param username: string to search in 'username' columns
        :param users_query: User model query to search
        :returns: User model query
        """
        query = (users_query
                 .filter(User.username.like('%' + username + '%')))
        return query


class Message(database.Model):
    """
    Message model.

    Static methods defined here:

    flush_messages(message_query)
    """
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
                + f'sender={self.sender}, '
                + f'recipient={self.recipient}, ' 
                + f'was_read={self.was_read}, '
                + f'text={self.text}, '
                + f'chat={self.chat}, '
                + f'date_created={self.date_created})'
               )
    
    @staticmethod  
    def flush_messages(message_query):
        """
        Set 'was_read' column to True for all messages from message_query.

        :param message_query: Message model query
        """
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

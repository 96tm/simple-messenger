from . import login_manager
from . import database
from .exceptions import ValidationError
from datetime import datetime, timezone
from itsdangerous import BadHeader, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import and_, not_
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from functools import partial
from werkzeug.security import generate_password_hash, check_password_hash


utc_now = partial(datetime.now, tz=timezone.utc)


@login_manager.user_loader
def load_user(user_id):
    """
    Set up current user.
    """
    return User.query.get(int(user_id))


def format_date(date):
    """
    Return a string representation of the given date.

    :param date: DateTime instance
    :returns: string
    """
    date_format = '%A, %B %d %Y %H:%M'
    return date.strftime(date_format)


def add_test_users():
    """
    Load data to the database
    for testing purposes.
    """
    database.create_all()
    arthur = User(username='Arthur', email='arthur@arthur.arthur',
                  password='arthurarthur', confirmed=True)
    morgain = User(username='Morgain', email='morgain@morgain.morgain',
                   password='morgainmorgain', confirmed=True)
    clair = User(username='Clair', email='clair@clair.clair',
                 password='clairclair', confirmed=True)
    merlin = User(username='Merlin', email='merlin@merlin.merlin',
                  password='merlinmerlin', confirmed=True)
    ophelia = User(username='Ophelia', email='ophelia@ophelia.ophelia',
                   password='opheliaophelia', confirmed=True)
    lancelot = User(username='Lancelot', email='lancelot@lancelot.lancelot',
                    password='lancelotlancelot', confirmed=True)
    guinevere = User(username='Guinevere', 
                     email='guinevere@guinevere.guinevere',
                     password='guinevereguinevere', confirmed=True)
    uther = User(username='Uther', 
                     email='uther@uther.uther',
                     password='utheruther', confirmed=True)
    mordred = User(username='Mordred', 
                   email='mordred@mordred.mordred',
                   password='mordredmordred', confirmed=True)
    percival = User(username='Percival', 
                    email='percival@percival.percival',
                    password='percivalpercival', confirmed=True)
    dinadan = User(username='Dinadan', 
                   email='dinadan@dinadan.dinadan',
                   password='dinadandinadan', confirmed=True)
    gingalain = User(username='Gingalain', 
                     email='gingalain@gingalain.gingalain',
                     password='gingalaingingalain', confirmed=True)
    galahad = User(username='Galahad', 
                   email='galahad@galahad.galahad',
                   password='galahadgalahad', confirmed=True)
    pelleas = User(username='Pelleas', 
                   email='pelleas@pelleas.pelleas',
                   password='pelleaspelleas', confirmed=True)
    pellinore = User(username='Pellinore', 
                     email='pellinore@pellinore.pellinore',
                     password='pellinorepellinore', confirmed=True)
    tristan = User(username='Tristan', 
                   email='tristan@tristan.tristan',
                   password='tristantristan', confirmed=True)
    branor = User(username='Branor', 
                  email='branor@branor.branor',
                  password='branorbranor', confirmed=True)
    accolon = User(username='Accolon', 
                   email='accolon@accolon.accolon',
                   password='accolonaccolon', confirmed=True)
    blanchefleur = User(username='Blanchefleur', 
                        email='blanchefleur@blanchefleur.blanchefleur',
                        password='blanchefleurblanchefleur', confirmed=True)
    brangaine = User(username='Brangaine', 
                     email='brangaine@brangaine.brangaine',
                     password='brangainebrangaine', confirmed=True)
    cailia = User(username='Caelia', 
                  email='caelia@caelia.caelia',
                  password='caeliacaelia', confirmed=True)
    dindrane = User(username='Dindrane', 
                    email='dindrane@dindrane.dindrane',
                    password='dindranedindrane', confirmed=True)
    enide = User(username='Enide', 
                 email='enide@enide.enide',
                 password='enideenide', confirmed=True)

    database.session.add_all([arthur, morgain, clair, merlin, ophelia,
                              lancelot, guinevere, mordred, percival,
                              dinadan, gingalain, galahad, pelleas,
                              pellinore, tristan, branor, accolon, cailia,
                              blanchefleur, brangaine, dindrane, enide,
                              uther])
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
    # permissions
    
    @staticmethod
    def insert_roles(roles=None):
        """
        Insert the given roles to the database.
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

    _date_created = database.Column(database.DateTime(timezone=True),
                                    default=utc_now)

    @hybrid_property
    def date_created(self):
        return self._date_created.astimezone(timezone.utc)
    
    @date_created.expression
    def date_created(self):
        return self._date_created
    
    @date_created.setter
    def date_created(self, value):
        self._data_created = value


class Chat(database.Model):
    """
    Represents a chat,
    which is defined as a collection of
    users and messages.
    

    Methods defined here:

    to_json(user)

    get_name(user)

    add_users(users)

    delete_users(users)


    Static methods defined here:

    from_json(json_object)

    search_chats_query(chat_name, user)


    Class methods defined here:
    
    get_chat(users)
    """
    __tablename__ = 'chats'
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(64))
    is_group_chat = database.Column(database.Boolean, default=False)
    _date_created = database.Column(database.DateTime(timezone=True),
                                    default=utc_now)
    _date_modified = database.Column(database.DateTime(timezone=True),
                                     default=utc_now,
                                     onupdate=utc_now)
    removed_users = database.relationship('RemovedChat',
                                          backref='chat',
                                          lazy='dynamic',
                                          cascade='all, delete-orphan')
    
    @hybrid_property
    def date_created(self):
        return self._date_created.astimezone(timezone.utc)
    
    @date_created.expression
    def date_created(self):
        return self._date_created
    
    @date_created.setter
    def date_created(self, value):
        self._date_created = value

    @hybrid_property
    def date_modified(self):
        return self._date_modified.astimezone(timezone.utc)
    
    @date_modified.expression
    def date_modified(self):
        return self._date_modified
    
    @date_modified.setter
    def date_modified(self, value):
        self._date_modified = value
    
    def to_json(self, user):
        """
        Return a JSON representation
        of current chat.

        :param user: current user (needed to get chat name)
        :returns: Chat model instance turned to dictionary
        """
        chat = {'chat_name': self.get_name(user),
                'is_group_chat': self.is_group_chat,
                'date_created': self.date_created,
                'date_modified': self.date_modified,
                'messages': url_for('api.get_messages', 
                                    chat_id=self.id,
                                    _external=True)
               }
        return chat

    def get_name(self, user):
        """
        Return current chat's 'name' if present,
        otherwise return 'username'
        of the first user of current chat's 'users' attribute
        which is not equal to the given user's username.

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
        Add the given users to current chat.

        :param users: sequence of User model instances
        """
        for user in users:
            if not user in self.users.all():
                self.users.append(user)
        database.session.commit()
    
    def remove_users(self, users):
        """
        Delete the given users from current chat.

        :param users: sequence of User model instances
        """
        for user in users:
            self.users.remove(user)
        database.session.commit()
    
    @staticmethod
    def from_json(json_chat, current_user):
        """
        Return a Chat model instance
        created from the given json_chat dictionary.

        :param json_chat: dictionary
        :param current_user: current user (needed to get chat name)
        :returns: Message model instance
        """
        chat = Chat()
        chat_name = json_chat.get('chat_name')
        usernames = json_chat.get('users')
        users = User.query.filter(User.username.in_(usernames)).all()
        if len(users) > 1:
            chat.is_group_chat = True
            if not chat_name:
                raise ValidationError('Chat name or recipient name\
                                       must be present.')
        chat.add_users(users)
        chat.add_users([current_user])
        return chat
    
    @staticmethod
    def search_chats_query(chat_name, user):
        """
        Return a query of chats
        where each chat either:
        - contains the given chat_name in 'name' column;
        - has only two users ('is_group_chat' is False and 'name' is None),
          and the user with 'username' not equal to (the given user).username
          contains the given chat_name in 'username'.

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
                                    .ilike('%' + chat_name + '%'))
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
                .filter(Chat.users.contains(user),
                        Chat.name.ilike('%' + chat_name + '%'))
                .union(chats))

    @classmethod
    def get_chat(cls, users):
        """
        Return the chat of users in the given sequence.

        :param user: sequence of User model instances
        :returns: Chat model instance
        """
        chat = cls.query
        for user in users:
            chat = chat.filter(cls.users.contains(user))
        return chat.first()

class User(UserMixin, database.Model):
    """
    User model. 
    Implements UserMixin, 
    used as a default authentication model by Flask-Login.


    Methods defined here:

    get_updated_chats(current_user, session)

    get_chat_query(user_ids)

    get_removed_query(chat_query=None)

    get_removed_chats_query(user_ids)

    mark_chats_as_removed(chats)

    unmark_chats_as_removed(chats)

    has_permission(permission)

    verify_password(password)

    generate_auth_token(expiration=3600)
    
    generate_confirmation_token(expiration=3600)
    
    confirm(token)
    
    has_contact(user)
    
    is_contacted_by(user)
    
    add_contacts(users, contact_group=None)
    
    delete_contacts(users)
    
    get_other_users_query()
    
    get_available_chats_query()
    
    get_messages(chat)
    
    get_unread_messages_query(chat)
    
    search_users_query(username, users_query)


    Static methods defined here:

    verify_auth_token(token)
    """
    __tablename__ = 'users'
    id = database.Column(database.Integer, primary_key=True)
    confirmed = database.Column(database.Boolean, default=False)
    last_seen = database.Column(database.DateTime(timezone=True), 
                                nullable=True)
    role_id = database.Column(database.Integer, 
                              database.ForeignKey('roles.id'))
    _date_created = database.Column(database.DateTime(timezone=True), 
                                    nullable=False,
                                    default=utc_now)
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
                                  backref=database.backref('users', 
                                                           lazy='dynamic'))
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

    @hybrid_property
    def date_created(self):
        return self._date_created.astimezone(timezone.utc)
    
    @date_created.expression
    def date_created(self):
        return self._date_created
    
    @date_created.setter
    def date_created(self, value):
        self._date_created = value
    
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
        Assign the given password to current user.

        :param password: string
        """
        self.password_hash = generate_password_hash(password)
    
    def get_updated_chats(self, current_user, session):
        """
        Return information about the user's updated chats,
        if there are any.

        :param current_user: the user currently logged in
        :param session: flask session
        :returns: dictionary with the keys 
                  'chats', 'current_chat_messages', 'current_username'
                  or None
        """
        available_chats = self.get_available_chats_query().all()
        chats = []
        messages = []
        for chat in available_chats:
            unread_messages_query = self.get_unread_messages_query(chat)
            count = unread_messages_query.count()
            if count:
                chats.append({'chat_id': str(chat.id),
                              'unread_messages_count': count,
                              'chat_name': chat.get_name(self)})
                current_chat_id = session.get((current_user.id, 
                                               'current_chat_id'))
                if current_chat_id == chat.id:
                    messages = (Message
                                .get_messages_list(unread_messages_query))
        if chats:
            data = {'chats': chats,
                    'current_chat_messages': messages,
                    'current_username': self.username}
            return data        

    def get_chat_query(self, user_ids):
        """
        Return a query of current user's chats 
        with users identified by the given user_ids.
        
        :param user_ids: sequence of integers
        :returns: Chat model query
        """
        return (Chat
                .query
                .filter(Chat.users.contains(self))
                .join(UserChatTable,
                      and_(UserChatTable.c.chat_id == Chat.id,
                           UserChatTable.c.user_id.in_(user_ids)
                          )
                    )
                )

    def get_removed_query(self, chat_query=None):
        """
        Return RemovedChat query for currrent user
        (based on the chat query, if given).

        :param chat_query: Chat model query
        :returns: RemovedChat model query
        """
        if chat_query:
            return (RemovedChat
                    .query
                    .filter(RemovedChat.user == self,
                            RemovedChat
                            .chat_id
                            .in_([chat.id
                                for chat
                                in chat_query.all()]
                                )
                            )
                    )
        else:
            return (RemovedChat
                    .query
                    .filter(RemovedChat.user==self))

    def get_removed_chats_query(self, user_ids):
        """
        Return a query of chats 
        with users having
        the given user_ids
        which are marked as removed by current user.
        
        :param user_ids: sequence of integers
        :returns: Chat model query
        """
        chat_query = self.get_chat_query(user_ids)
        removed_chat_query = self.get_removed_query(chat_query)
        result = (chat_query
                  .join(removed_chat_query.subquery(),
                        Chat
                        .id
                        .in_([removed.chat_id 
                              for removed
                              in removed_chat_query]
                            )
                       )
                 )
        return result
    
    def mark_chats_as_removed(self, chats):
        """
        Add RemovedChat record
        for each chat in the given chats.
        
        :param chats: sequence of Chat model instances
        """
        for chat in chats:
            removed_chat = RemovedChat()
            removed_chat.user = self
            removed_chat.chat = chat
            database.session.add(removed_chat)
        database.session.commit()
    
    def unmark_chats_as_removed(self, chats):
        """
        Delete RemovedChat record
        for each chat in the given chats.
        
        :param chats: sequence of Chat model instances
        """
        chat_ids = [chat.id for chat in chats]
        removed_chats_query = (RemovedChat
                                .query
                                .filter(RemovedChat.chat_id.in_(chat_ids),
                                        RemovedChat.user_id == self.id))
        removed_chats_query.delete(synchronize_session='fetch')
    
    def has_permission(self, permission):
        """
        Check if current user has the given permission.

        :param permission: integer representing permission
        :returns: True if current user has a role
                  and the role has permission,
                  False otherwise

        """
        return (self.role is not None
                and (self.role.permissions & permission == permission))
    
    def verify_password(self, password):
        """
        Check if the given password matches current user's password.

        :param password: string
        :returns: True if password matches current user's password, 
                  False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def generate_auth_token(self, expiration=3600):
        """
        Return an authentication token for current user.

        :param expiration: Time in seconds after which token expires
        :returns: TimedJSONWebSignature
        """
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'id': self.id})
    
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
        Check that the given token belongs to current user
        and set current user's 'confirmed' column to True
        if it does.

        :param token: TimedJSONWebSignature instance or string
        :returns: True if the given token belongs to current user,
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
        Check if current user has the given user as a contact.

        :param user: User model instance
        :returns: True if current user has user as a contact,
                  False otherwise
        """
        return bool(self.contacts.filter_by(contact_id=user.id).first())
    
    def is_contacted_by(self, user):
        """
        Check if the given user has current user as a contact.

        :param user: User model instance
        :returns: True if user has current user as a contact,
                  False otherwise
        """
        return bool(self.contacted.filter_by(user_id=user.id).first())
    
    def add_contacts(self, users, contact_group=None):
        """
        Add  the given users to current user's contacts.

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
        Delete the given users from contacts of current user.

        :param users: sequence of User model instances
        """
        for user in users:
            if self.has_contact(user):
                relation = self.contacts.filter_by(contact_id=user.id).first()
                database.session.delete(relation)
    
    def get_other_users_query(self):
        """
        Return a query of users not including current user
        ordered by column 'username' in ascending order.

        :returns: User model query
        """
        return (User
                .query
                .filter(User.id != self.id)
                .order_by(User.username))
    
    def get_available_chats_query(self):
        """
        Return a query of current user's chats 
        not marked as removed ordered by modification date
        in descending order.

        :returns: User model query
        """
        removed_chats = self.get_removed_query()
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
        sorted by creation date in ascending order.

        :param chat: Chat model instance
        :returns: list of dictionaries
        """
        messages = chat.messages.order_by(Message.date_created).all()
        message_dict_list = []
        for message in messages:
            sender = message.sender
            recipient = message.recipient
            sender_name = sender.username if sender else None
            recipient_name = recipient.username if recipient else None
            message_dict = {'text': message.text,
                            'date_created': message.date_created.isoformat(),
                            'sender_username': sender_name,
                            'recipient_username': recipient_name}
            message_dict_list.append(message_dict)
        return message_dict_list
    
    def get_unread_messages_query(self, chat):
        """
        Return a query of unread messages from the given chat.

        :param chat: Chat model instance
        :returns: Message model query
        """
        return (chat
                .messages
                .filter(Message.sender != self,
                        not_(Message.was_read)))

    def search_users_query(self, username, users_query):
        """
        Return a query of users (except current user) 
        from the given users_query
        containing the given username string in the 'username' column
        in ascending lexicographical order by 'username'.

        :param username: string to search in 'username' columns
        :param users_query: User model query to search
        :returns: User model query
        """
        query = (users_query
                 .filter(User.username.ilike('%' + username + '%')))
        return query
    
    @staticmethod
    def verify_auth_token(token):
        """
        Check the valididty of given token.

        :param token: TimedJSONWebSignature
        :returns: True if token is valid, 
                  False otherwise
        """
        print('user verify function')
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            print('hey')
            data = serializer.loads(token)
            print('data', data)
        except Exception as exception:
            print(exception)
            return None
        print(data)
        return User.query.get(data['id'])


class Message(database.Model):
    """
    Message model.


    Methods defined here:

    to_json(user)


    Static methods defined here:

    get_messages_list(message_query)

    from_json(json_message)

    flush_messages(message_query)
    """
    __tablename__ = 'messages'
    id = database.Column(database.Integer, primary_key = True)
    was_read = database.Column(database.Boolean,
                               default=False)
    text = database.Column(database.Text)
    _date_created = database.Column(database.DateTime(timezone=True),
                                     nullable=False,
                                     default=utc_now)
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
    
    @hybrid_property
    def date_created(self):
        return self._date_created.astimezone(timezone.utc)

    @date_created.expression
    def date_created(self):
        return self._date_created

    @date_created.setter
    def date_created(self, value):
        self._date_created = value

    def to_json(self, user):
        """
        Return a dictionary representation
        of current message.

        :param user: current user (needed to get the chat name)
        :returns: Message model instance turned into a dictionary
        """
        if not self.recipient:
            recipient_username = ''
        else:
            recipient_username = self.recipient.username
    
        message = {'id': self.id,
                   'chat_id': self.chat_id,
                   'was_read': self.was_read,
                   'date_created': self.date_created,
                   'text': self.text,
                   'sender_username': self.sender.username,
                   'recipient_username': recipient_username,
                   'chat_name': self.chat.get_name(user)}
        return message
    
    @staticmethod
    def get_messages_list(message_query):
        """
        Return a list of dictionaries with keys 
        'text', 'sender_username', 'date_created'
        for the messages from the given message_query
        sorted by modification date in ascending order.

        :param message_query: Message model query
        :returns: list of dictionaries
        """

        message_dict_list = []
        for message in message_query.order_by(Message.date_created).all():
            sender = message.sender
            sender_username = sender.username if sender else None
            date_created = message.date_created
            message_dict = {'text': message.text,
                            'sender_username': sender_username,
                            'date_created': date_created.isoformat()}
            message_dict_list.append(message_dict)
        return message_dict_list
    
    @staticmethod
    def from_json(json_message):
        """
        Return a Message model instance
        created from the give json_message dictionary.

        :param json_message: dictionary
        :returns: Message model instance
        """
        try:
            text = str(json_message.get('text')).rstrip()
            if text:
                message = Message()
                message.text = text[:current_app.config['MAX_STRING_LENGTH']]
                return message
        except (LookupError, ValueError):
            pass

    @staticmethod  
    def flush_messages(message_query):
        """
        Set 'was_read' column to True for all messages 
        from the given message_query.

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

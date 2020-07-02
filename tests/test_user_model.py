import time

from app import create_app, database
from app.models import Contact, Chat, format_date, Message
from app.models import User, UserChatTable, Role, Permission
from flask import current_app
import unittest


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        database.create_all()
        Role.insert_roles()

        self.bob = User(username='bob', password='bob',
                        email='bob@bob.bob', confirmed=True)
        self.arthur = User(username='arthur', password='arthur',
                           email='arthur@arthur.arthur', confirmed=True)
        self.clair = User(username='clair', password='clair',
                          email='clair@clair.clair', confirmed=True)
        self.morgana = User(username='morgana', password='morgana',
                            email='morgana@morgana.morgana', confirmed=True)
        self.ophelia = User(username='ophelia', password='ophelia',
                            email='ophelia@ophelia.ophelia', confirmed=True)

        self.chat_bob_arthur = Chat()
        self.chat_bob_clair = Chat()
        self.chat_morgana_arthur = Chat()
        self.chat_morgana_bob = Chat()
        self.chat_bob_arthur.add_users([self.bob, self.arthur])
        self.chat_bob_clair.add_users([self.bob, self.clair])
        self.chat_morgana_arthur.add_users([self.arthur, self.morgana])
        self.chat_morgana_bob.add_users([self.bob, self.morgana])

        self.bob.add_contacts([self.clair])
        self.bob.add_contacts([self.morgana])

        database.session.add_all([self.bob, self.arthur, self.ophelia,
                                  self.clair, self.morgana, 
                                  self.chat_bob_arthur,
                                  self.chat_bob_clair,
                                  self.chat_morgana_arthur,
                                  self.chat_morgana_bob])
        database.session.commit()
    
    def tearDown(self):
        database.session.remove()
        database.drop_all()
        self.app_context.pop()

    def t1est_expired_confirmation_token(self):
        user = User(password='pass', email='user@user.user', username='user')
        database.session.add(user)
        database.session.commit()
        token = user.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(user.confirm(token))

    def test_password_setter(self):
        self.assertTrue(self.bob.password_hash is not None)
    
    def test_no_password_getter(self):
        user = User(username='user', email='user@user.user', password='pass')
        with self.assertRaises(AttributeError):
            user.password
    
    def test_password_verification(self):
        self.assertTrue(self.bob.verify_password('bob'))
        self.assertFalse(self.bob.verify_password('wrong'))

    def test_passwords_salts_are_random(self):
        self.assertTrue(self.bob.password_hash != self.clair.password_hash)
    
    def test_add_contacts(self):
        self.assertEqual(self.clair, 
                         (self
                         .bob
                         .contacts
                         .filter_by(contact_id=self.clair.id)
                         .first()
                         .contact))
        self.assertTrue(self.bob.has_contact(self.clair))
        self.assertFalse(self.clair.has_contact(self.bob))
        self.assertTrue(self.clair.is_contacted_by(self.bob))
        self.assertTrue(self.bob.contacts.count() == 2)
        self.assertTrue(self.clair.contacted.count() == 1)
        self.assertTrue(Contact.query.count() == 2)
    
    def test_has_contact(self):
        self.assertTrue(self.bob.has_contact(self.clair))
        self.assertFalse(self.bob.has_contact(self.arthur))
    
    def test_is_contacted_by(self):
        self.assertTrue(self.clair.is_contacted_by(self.bob))
        self.assertFalse(self.arthur.is_contacted_by(self.bob))
        
    def test_delete_contacts(self):
        self.bob.delete_contacts([self.clair])
        database.session.commit()
        self.assertTrue(Contact.query.count() == 1)
        self.assertTrue(self.bob.contacts.count() == 1)
        self.assertTrue(self.clair.contacted.count() == 0)
        self.assertFalse(self.bob.has_contact(self.clair))
        self.assertFalse(self.clair.is_contacted_by(self.bob))
    
    def test_confirm_user(self):
        user1 = User(username='user1', email='user1@user.user', password='pass')
        user2 = User(username='user2', email='user2@user.user', password='pass')
        user1.id = 1
        user2.id = 2
        token1 = user1.generate_confirmation_token()
        token2 = user2.generate_confirmation_token()
        self.assertFalse(user1.confirm(token2))
        self.assertTrue(user1.confirm(token1))
    
    def test_roles(self):
        Role.insert_roles()
        user = User(username='user', email='user@user.user', password='user')
        admin = User(username='admin', email=current_app.config['ADMIN_MAIL'], password='admin')
        self.assertEqual(user.role, Role.query.filter_by(is_default=True).first())
        self.assertEqual(user.role, Role.query.filter_by(name='User').first())
        self.assertEqual(admin.role, Role.query.filter_by(name='Admin').first())

    def test_permissions(self):
        Role.insert_roles()
        user = User(username='user', email='user@user.user', password='user')
        admin = User(username='admin', email=current_app.config['ADMIN_MAIL'], password='admin')
        self.assertFalse(user.has_permission(Permission.ADMINISTRATION))
        self.assertTrue(admin.has_permission(Permission.ADMINISTRATION))
    
    def test_chat_two_users_1(self):
        message1 = Message(text='hi there1', sender=self.arthur, 
                           recipient=self.bob, was_read=True, 
                           chat=self.chat_bob_arthur)
        message2 = Message(text='hi there2', sender=self.arthur, 
                           recipient=self.bob, was_read=True, 
                           chat=self.chat_bob_arthur)
        message3 = Message(text='hi there3', sender=self.arthur, 
                           recipient=self.bob, chat=self.chat_bob_arthur)
        message4 = Message(text='hi there4', sender=self.arthur,
                           recipient=self.bob, chat=self.chat_bob_arthur)
        database.session.add_all([message1, message2, message3, message4])
        database.session.commit()

        user_chats = (database
                      .session
                      .query(Chat)
                      .join(UserChatTable, 
                            (UserChatTable.c.user_id==self.bob.id) 
                            & (UserChatTable.c.chat_id==Chat.id))
                      .subquery())

        found_chat = (database
                     .session
                     .query(Chat)
                     .join(UserChatTable, 
                           (UserChatTable.c.user_id==self.arthur.id) 
                           & (UserChatTable.c.chat_id==Chat.id))
                     .join(user_chats).first())
        self.assertEqual(self.chat_bob_arthur, found_chat)

    def test_chat_two_users_2(self):
        message1 = Message(text='hi there1', sender=self.arthur,
                           recipient=self.bob, 
                           was_read=True, chat=self.chat_bob_arthur)
        message2 = Message(text='hi there2', sender=self.arthur,
                           recipient=self.bob, was_read=True, chat=self.chat_bob_arthur)
        message3 = Message(text='hi there3', sender=self.arthur,
                           recipient=self.bob, chat=self.chat_bob_arthur)
        message4 = Message(text='hi there4', sender=self.arthur,
                           recipient=self.bob, chat=self.chat_bob_arthur)

        message5 = Message(text='hi there5', sender=self.morgana,
                           recipient=self.arthur, chat=self.chat_bob_clair)
        message6 = Message(text='hi there6', sender=self.bob,
                           recipient=self.clair, chat=self.chat_morgana_arthur)

        database.session.add_all([message1, message2, 
                                  message3, message4, 
                                  message5, message6])
        database.session.commit()

        user_chats = (database
                     .session
                     .query(Chat)
                     .join(UserChatTable, 
                           (UserChatTable.c.user_id==self.bob.id) 
                           & (UserChatTable.c.chat_id==Chat.id))
                     .subquery())

        found_chat = (database
                     .session
                     .query(Chat)
                     .join(UserChatTable, 
                           (UserChatTable.c.user_id==self.arthur.id) 
                           & (UserChatTable.c.chat_id==Chat.id))
                     .join(user_chats).first())
        self.assertEqual(set(found_chat.messages),
                         set([message1, message2, message3, message4]))
        self.assertEqual(self.chat_bob_arthur, found_chat)

    def test_get_other_users_query(self):
        bob_other_users = self.bob.get_other_users_query().all()
        self.assertIn(self.clair,
                      bob_other_users)
        self.assertIn(self.morgana,
                      bob_other_users)
        self.assertIn(self.arthur,
                      bob_other_users)
        self.assertEqual(len(bob_other_users),
                         User.query.count() - 1)

    def test_get_available_chats_query(self):
        chats = self.bob.get_available_chats_query().all()
        self.assertEqual(chats,
                         (Chat
                          .query
                          .filter(Chat.users.contains(self.bob)).all()))
        Chat.mark_chats_as_removed(self.bob, [self.chat_bob_arthur])
        chats = self.bob.get_available_chats_query().all()
        self.assertNotEqual(chats,
                            (Chat
                             .query
                             .filter(Chat.users.contains(self.bob)).all()))
        self.assertNotIn(self.chat_bob_arthur,
                         chats)
        self.assertEqual(len(chats),
                         (Chat
                          .query
                          .filter(Chat.users.contains(self.bob)).count() - 1))

    def test_get_messages(self):
        message1 = Message(text='hi arthur', 
                           sender=self.bob, recipient=self.arthur,
                           chat=self.chat_bob_arthur, was_read=True)
        message2 = Message(text='hi bob', 
                           sender=self.arthur, recipient=self.bob,
                           chat=self.chat_bob_arthur)
        message3 = Message(text='what\'s up', 
                           sender=self.arthur, recipient=self.bob,
                           chat=self.chat_bob_arthur)
        database.session.add_all([message1, message2, message3])
        database.session.commit()
        message_dict_1 = {
                            'text':message1.text,
                            'date_created': message1.date_created,
                            'sender_username': message1.sender.username,
                            'recipient_username': message1.recipient.username
                         }
        message_dict_2 = {
                            'text':message2.text,
                            'date_created': message2.date_created,
                            'sender_username': message2.sender.username,
                            'recipient_username': message2.recipient.username
                         }
        message_dict_3 = {
                            'text':message3.text,
                            'date_created': message3.date_created,
                            'sender_username': message3.sender.username,
                            'recipient_username': message3.recipient.username
                         }        
        messages = self.bob.get_messages(self.chat_bob_arthur)
        self.assertIn(message_dict_1, messages)
        self.assertIn(message_dict_2, messages)
        self.assertIn(message_dict_3, messages)
        self.assertEqual(len(messages), 3)
        self.assertTrue(message1.was_read)
        self.assertTrue(message2.was_read)
        self.assertTrue(message3.was_read)

    def test_get_unread_messages(self):
        message1 = Message(text='hi arthur', 
                           sender=self.bob, recipient=self.arthur,
                           chat=self.chat_bob_arthur, was_read=True)
        message2 = Message(text='hi bob', 
                           sender=self.arthur, recipient=self.bob,
                           chat=self.chat_bob_arthur)
        message3 = Message(text='what\'s up', 
                           sender=self.arthur, recipient=self.bob,
                           chat=self.chat_bob_arthur)
        message4 = Message(text='see you', 
                           sender=self.arthur, recipient=self.bob,
                           chat=self.chat_bob_arthur, was_read=True)
        database.session.add_all([message1, message2, message3, message4])
        database.session.commit()
        message_dict_2 = {
                            'text':message2.text,
                            'sender_username': message2.sender.username,
                            'date_created': message2.date_created
                         }
        message_dict_3 = {
                            'text':message3.text,
                            'sender_username': message3.sender.username,
                            'date_created': message3.date_created
                         }        
        messages = self.bob.get_unread_messages(self.chat_bob_arthur)
        self.assertIn(message_dict_2, messages)
        self.assertIn(message_dict_3, messages)
        self.assertEqual(len(messages), 2)
        self.assertTrue(message1.was_read)
        self.assertTrue(message2.was_read)
        self.assertTrue(message3.was_read)

    def test_search_users_query(self):
        other_users_query = self.bob.get_other_users_query()
        artorias = User(username='artorias', 
                        password='artorias',
                        email='artorias@artorias.artorias', 
                        confirmed=True)
        self.assertEqual(self.bob
                         .search_users_query('bob', other_users_query)
                         .all(), [])
        self.assertIn(self.morgana,
                      self.bob
                      .search_users_query('morgana', other_users_query)
                      .all())                      
        self.assertIn(self.arthur,
                      self.bob
                      .search_users_query('art', other_users_query)
                      .all())
        self.assertIn(artorias,
                      self.bob
                      .search_users_query('art', other_users_query)
                      .all())
        self.assertEqual(self
                         .bob
                         .search_users_query('art', other_users_query)
                         .count(), 2)

import time

from app import create_app, database
from app.models import Contact, Chat, format_date, Message
from app.models import User, UserChatTable, Role, Permission
from flask import current_app
import unittest


class MessageModelTestCase(unittest.TestCase):
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

        self.chat_bob_arthur = Chat()
        self.chat_bob_arthur.add_users([self.bob, self.arthur])

        self.message1 = Message(text='hi there1', 
                                sender=self.arthur, 
                                recipient=self.bob,
                                was_read=True, 
                                chat=self.chat_bob_arthur)
        self.message2 = Message(text='hi there2', 
                                sender=self.arthur, 
                                recipient=self.bob,
                                chat=self.chat_bob_arthur)
        self.message3 = Message(text='hi there3', 
                                sender=self.arthur, 
                                recipient=self.bob, 
                                chat=self.chat_bob_arthur)
        self.message4 = Message(text='hi there4', 
                                sender=self.bob, 
                                recipient=self.arthur, 
                                chat=self.chat_bob_arthur)

        database.session.add_all([self.bob, self.arthur,
                                  self.chat_bob_arthur,
                                  self.message1,
                                  self.message2,
                                  self.message3,
                                  self.message4])
        database.session.commit()
    
    def tearDown(self):
        database.session.remove()
        database.drop_all()
        self.app_context.pop()
    
    def test_flush_messages(self):
        self.assertFalse(self.message2.was_read)
        self.assertFalse(self.message3.was_read)
        self.assertTrue(self.message1.was_read)
        self.assertFalse(self.message4.was_read)
        Message.flush_messages(Message
                               .query
                               .filter(Message.sender == self.arthur))
        self.assertTrue(self.message2.was_read)
        self.assertTrue(self.message3.was_read)
        self.assertTrue(self.message1.was_read)
        self.assertFalse(self.message4.was_read)

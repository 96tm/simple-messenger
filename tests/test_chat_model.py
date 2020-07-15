from app import create_app, database
from app.models import Chat, User, Role
from flask import url_for
import unittest
from app.exceptions import ValidationError


class ChatModelTestCase(unittest.TestCase):
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
        self.artorias = User(username='artorias', password='artorias',
                             email='artorias@artorias.artorias', confirmed=True)

        self.chat_bob_arthur = Chat()
        self.chat_bob_artorias = Chat()
        self.chat_bob_clair = Chat()
        self.chat_morgana_arthur = Chat()
        self.chat_morgana_bob = Chat(name='chat_morgana_bob_')
        self.chat_bob_arthur.add_users([self.bob, self.arthur])
        self.chat_bob_artorias.add_users([self.bob, self.artorias])
        self.chat_bob_clair.add_users([self.bob, self.clair])
        self.chat_morgana_arthur.add_users([self.arthur, self.morgana])
        self.chat_morgana_bob.add_users([self.bob, self.morgana])
        database.session.add_all([self.bob, self.arthur, self.ophelia,
                                  self.artorias,
                                  self.clair, self.morgana, 
                                  self.chat_bob_arthur,
                                  self.chat_bob_artorias,
                                  self.chat_bob_clair,
                                  self.chat_morgana_arthur,
                                  self.chat_morgana_bob])
        database.session.commit()

    def tearDown(self):
        database.session.remove()
        database.drop_all()
        self.app_context.pop()

    def test_add_users(self):
        chat = Chat()
        chat.add_users([self.bob, self.arthur])
        self.assertIn(self.bob, chat.users.all())
        self.assertIn(self.arthur, chat.users.all())
        self.assertEqual(chat.users.count(), 2)
    
    def test_remove_users(self):
        chat = Chat()
        chat.add_users([self.bob, self.clair, self.morgana])
        self.assertEqual(chat.users.count(), 3)
        self.assertIn(self.bob, chat.users.all())
        chat.remove_users([self.bob])
        self.assertEqual(chat.users.count(), 2)
        self.assertNotIn(self.bob, chat.users.all())
        chat.remove_users([self.morgana, self.clair])
        self.assertEqual(chat.users.count(), 0)

    def test_get_chat(self):
        self.assertEqual(Chat.get_chat([self.bob, self.arthur]),
                         self.chat_bob_arthur)
        self.assertEqual(Chat.get_chat([self.clair, self.bob]),
                         self.chat_bob_clair)
        self.assertEqual(Chat.get_chat([self.arthur, self.morgana]),
                         self.chat_morgana_arthur)
   
    def test_get_name(self):
        self.assertEqual(self.chat_morgana_bob.get_name(self.bob),
                         self.chat_morgana_bob.name)
        self.assertEqual(self.chat_morgana_bob.get_name(self.morgana),
                         self.chat_morgana_bob.name)
        self.assertEqual(self.chat_bob_arthur.get_name(self.bob),
                         self.arthur.username)
        self.assertEqual(self.chat_bob_arthur.get_name(self.arthur),
                         self.bob.username)

    def test_search_chats_query(self):
        chats = Chat.search_chats_query('mor', self.bob).all()
        self.assertIn(self.chat_morgana_bob, chats)
        self.assertEqual(len(chats), 1)
        self.chat_morgana_bob.name = 'chat'
        chats = Chat.search_chats_query('chat', self.bob).all()
        self.assertIn(self.chat_morgana_bob, chats)
        self.assertEqual(len(chats), 1)
        chats = Chat.search_chats_query('wrong', self.bob).all()
        self.assertEqual(len(chats), 0)
        chats = Chat.search_chats_query('art', self.bob).all()
        self.assertIn(self.chat_bob_arthur, chats)
        self.assertIn(self.chat_bob_artorias, chats)
        self.assertEqual(len(chats), 2)

    def test_from_json(self):
        json_chat = {'chat_name': None,
                     'users': ['morgana']}
        chat = Chat.from_json(json_chat, self.clair)
        self.assertEqual(chat.name, None)
        self.assertEqual(chat.get_name(self.clair), self.morgana.username)
        self.assertEqual(chat.get_name(self.morgana), self.clair.username)
        self.assertIn(self.clair, chat.users.all())
        self.assertIn(self.morgana, chat.users.all())
        json_chat = {'chat_name': None,
                     'users': ['morgana', 'bob']}
        with self.assertRaises(ValidationError):
            Chat.from_json(json_chat, self.clair)

    def test_to_json(self):
        chat = self.chat_bob_arthur
        self.app.config['SERVER_NAME'] = 'localhost'
        with self.app.app_context():
            json_chat = chat.to_json(self.bob)
            self.assertEqual(json_chat,
                            {'chat_name': self.arthur.username,
                            'is_group_chat': chat.is_group_chat,
                            'date_created': chat.date_created,
                            'date_modified': chat.date_modified,
                            'messages': url_for('api.get_messages', 
                                        chat_id=chat.id,
                                        _external=True)
                            })
        del self.app.config['SERVER_NAME']

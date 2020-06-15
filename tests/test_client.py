from datetime import datetime, timezone
import time

from app import create_app, database
from app.models import User, Role, Permission, Contact, Message
from app.main.views import check_new_messages
from app.auth.forms import LoginForm
from flask import current_app, json, jsonify
import unittest


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        database.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def test_register_and_login(self):
        response = self.client.post('/auth/signup', data={
            'email': 'no_such_email@gmail.com',
            'username': 'user',
            'password': 'pass',
            'password_confirmation': 'pass'
        })
        self.assertEqual(response.status_code, 302)

        user = User.query.filter_by(username='user').first()
        print('USER', user)

        response = self.client.post('/auth/login', data={
            'email': 'user@user.user',
            'password': 'pass'
        }, follow_redirects=True)
        self.assertIn('Invalid', response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/auth/login', data={
            'email': 'no_such_email@gmail.com',
            'password': 'pass'
        }, follow_redirects=True)
        self.assertIn('Hello', response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)

        user = User(username='confirmed_user', password ='pass',
                email='confirmed@confirmed.confirmed', confirmed=True)
        database.session.add(user)
        database.session.commit()

        response = self.client.post('/auth/login', data={
            'email': 'confirmed@confirmed.confirmed',
            'password': 'pass'
        }, follow_redirects=True)
        self.assertIn(f'SimpleChat - {user.username}',
                      response.get_data(as_text=True))

    
    def test_check_new_messages(self):
        bob = User(username='bob', password='bob', email='bob@bob.bob', confirmed=True)
        arthur = User(username='arthur', password='arthur', email='arthur@arthur.arthur', confirmed=True)
        database.session.add_all([bob, arthur])
        database.session.commit()
        message1 = Message(text='hi there1', sender=arthur, recipient=bob, was_read=True)
        message2 = Message(text='hi there2', sender=arthur, recipient=bob, was_read=True)
        message3 = Message(text='hi there3', sender=arthur, recipient=bob)
        message4 = Message(text='hi there4', sender=arthur, recipient=bob)
        database.session.add_all([message1, message2, message3, message4])
        database.session.commit()
        data = {'email': bob.email, 'remember_me': True, 'password': 'bob'}
        self.client.post('/auth/login', data=data)
        
        response = self.client.post('/check_new_messages',
                                    content_type='application/json',
                                    headers=[('X-Requested-With',
                                              'XMLHttpRequest')],
                                    json={'contact_id': arthur.id},
                                    follow_redirects=True)
        self.assertTrue(message3.was_read)
        self.assertTrue(message4.was_read)

    def tearDown(self):
        database.session.remove()
        database.drop_all()
        self.app_context.pop()

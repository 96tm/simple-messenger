from datetime import datetime, timezone
import time

from app import create_app, database
from app.models import User, Role, Permission, Contact
from flask import current_app
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
        # register a new account
        response = self.client.post('/auth/signup', data={
            'email': 'user@user.user',
            'username': 'username',
            'password': 'pass',
            'password2': 'pass'
        })
        self.assertEqual(response.status_code, 200)

        user = User(username='username', password='pass', email='user@user.user', confirmed=True)
        database.session.add(user)
        database.session.commit()

        # login with the new account
        response = self.client.post('/auth/login', data={
            'email': 'user@user.user',
            'password': 'pass'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        database.session.remove()
        database.drop_all()
        self.app_context.pop()

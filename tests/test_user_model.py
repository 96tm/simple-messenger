from datetime import datetime, timezone
import time

from app import create_app, database
from app.models import User, Role, Permission, Contact
from flask import current_app
import unittest


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        database.create_all()
        Role.insert_roles()
    
    def tearDown(self):
        database.session.remove()
        database.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        user = User(username='user', email='user@user.user', password='pass')
        self.assertTrue(user.password_hash is not None)
    
    def test_no_password_getter(self):
        user = User(username='user', email='user@user.user', password='pass')
        with self.assertRaises(AttributeError):
            user.password
    
    def test_password_verification(self):
        user = User(username='user', email='user@user.user', password='pass')
        self.assertTrue(user.verify_password('pass'))
        self.assertFalse(user.verify_password('shall not pass'))

    def test_passwords_salts_are_random(self):
        user1 = User(username='user', email='user@user.user', password='pass')
        user2 = User(username='user', email='user@user.user', password='pass')
        self.assertTrue(user1.password_hash != user2.password_hash)
    
    def test_add_contacts(self):
        user1 = User(username='duke', confirmed=True,
                     email='duke@duke.duke',
                     password='duke')
        user2 = User(username='craig', confirmed=True,
                     email='craig@craig.craig',
                     password='craig')
        user3 = User(username='sophia', confirmed=True,
                     email='sophia@sophia.sophia',
                     password='sophia')
        database.session.add_all((user1, user2, user3))
        database.session.commit()
        user1.add_contact(user2)
        user1.add_contact(user3)
        database.session.commit()
        
        self.assertEqual(user2, user1.contacts.filter_by(contact_id=user2.id).first().contact)
        self.assertTrue(user1.has_contact(user3))
        self.assertFalse(user2.has_contact(user1))
        self.assertTrue(user2.is_contacted_by(user1))
        self.assertTrue(user1.contacts.count() == 2)
        self.assertTrue(user2.contacted.count() == 1)
        self.assertTrue(Contact.query.count() == 2)
        user1.delete_contact(user2)
        database.session.commit()
        self.assertTrue(Contact.query.count() == 1)
        self.assertTrue(user1.contacts.count() == 1)
        self.assertTrue(user2.contacted.count() == 0)
        self.assertFalse(user1.has_contact(user2))
        self.assertFalse(user2.is_contacted_by(user1))
    
    def test_confirm_user(self):
        user1 = User(username='user1', email='user1@user.user', password='pass')
        user2 = User(username='user2', email='user2@user.user', password='pass')
        user1.id = 1
        user2.id = 2
        token1 = user1.generate_confirmation_token()
        token2 = user2.generate_confirmation_token()
        self.assertFalse(user1.confirm(token2))
        self.assertTrue(user1.confirm(token1))
    
    def test_expired_confirmation_token(self):
        user = User(password='pass', email='user@user.user', username='user')
        database.session.add(user)
        database.session.commit()
        token = user.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(user.confirm(token))
    
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

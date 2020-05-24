from app import create_app, database
from app.models import User, Role
from flask import current_app
import unittest


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        database.create_all()
    
    def tearDown(self):
        database.session.remove()
        database.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        user = User(password='pass')
        self.assertTrue(user.password_hash is not None)
    
    def test_no_password_getter(self):
        user = User(password='pass')
        with self.assertRaises(AttributeError):
            user.password
    
    def test_password_verification(self):
        user = User(password='pass')
        self.assertTrue(user.verify_password('pass'))
        self.assertFalse(user.verify_password('shall not pass'))

    def test_passwords_salts_are_random(self):
        user1 = User(password='pass')
        user2 = User(password='pass')
        self.assertTrue(user1.password_hash != user2.password_hash)
    
    def test_add_contacts(self):
        user1 = User()
        user2 = User()
        user3 = User()
        user1.add_contact(user2)
        user1.add_contact(user3)
        self.assertIn(user2, user1.contacts)
        self.assertIn(user3, user1.contacts)
    
    def test_confirm_user(self):
        user1 = User()
        user2 = User()
        user1.id = 1
        user2.id = 2
        token1 = user1.generate_confirmation_token()
        token2 = user2.generate_confirmation_token()
        self.assertFalse(user1.confirm(token2))
        self.assertTrue(user1.confirm(token1))
    
    def test_roles_and_permissions(self):
        Role.insert_roles()
        user = User(username='user', email='user@user.user', password='user')
        self.assertEqual(user.role, Role.query.filter_by(is_default=True).first())
        self.assertEqual(user.role, Role.query.filter_by(name='User').first())
        admin = User(username='admin', email=current_app.config['ADMIN_MAIL'], password='admin')
        self.assertEqual(admin.role, Role.query.filter_by(name='Admin').first())

from app.models import User
import unittest


class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        user = User(password='pass')
        self.assertTrue(user.password_hash is not None)
    
    def test_no_password_getter(self):
        user = User(password='pass')
        with self.assertRaise(AttributeError):
            user.password
    
    def test_password_verification(self):
        user = User(password='pass')
        self.assertTrue(user.verify_password('pass'))
        self.assertFalse(user.verify_password('shall not pass'))

    def test_passwords_salts_are_random(self):
        user1 = User(password='pass')
        user2 = User(password='pass')
        self.assertTrue(user1.password_hash != user2.password_hash)
    
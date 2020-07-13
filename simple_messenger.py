import click

from app import create_app, database, socket_io
from app.models import UserChatTable, Chat, add_test_data, RemovedChat
from app.models import User, Role, Contact, Message
from config import ProductionConfig
import gevent
from flask import request


app = create_app(ProductionConfig.name)
            

@app.cli.command('test')
def test_all():
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.shell_context_processor
def make_shell_context():
    return {'database': database,
            'UserChatTable': UserChatTable,
            'Chat': Chat,
            'User': User,
            'Role': Role,
            'RemovedChat': RemovedChat,
            'Contact': Contact, 
            'Message': Message,
            'bob': User.query.filter_by(username='bob').first(),
            'add_test_data': add_test_data,
            'arthur': User.query.filter_by(username='arthur').first()}


if __name__ == '__main__':
    socket_io.run(app, debug=True)

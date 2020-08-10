from app import celery, create_app, database, socket_io
from app.models import add_test_users as add_users
from app.models import UserChatTable, Chat, RemovedChat
from app.models import User, Role, Contact, Message
from sqlalchemy.exc import IntegrityError


app = create_app()


@app.cli.command('add_test_users', help='Add test users to the database.')
def add_test_users():
    try:
        add_users()
    except IntegrityError:
        database.session.rollback()
        return


@app.cli.command('test', help='Run all tests.')
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
            'Message': Message}


if __name__ == '__main__':
    socket_io.run(app, debug=False)

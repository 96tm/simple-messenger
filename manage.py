import os
from app import create_app, database
from app.models import User, Role
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

wsgi_application = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(wsgi_application)
migrate = Migrate(wsgi_application, database)

def make_shell_context():
    return dict(app=wsgi_application, User=User, Role=Role)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('database', MigrateCommand)

if __name__ == '__main__':
    manager.run()

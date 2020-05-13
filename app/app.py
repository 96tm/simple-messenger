from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
import os


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = ('postgresql://' 
                                         + os.environ['FLASK_DB_USER']
                                         + ':' 
                                         + os.environ['FLASK_DB_PASS']
                                         + '@'
                                         + os.environ['FLASK_DB_HOSTNAME'] + '/'
                                         + 'simple_chat_db')
db = SQLAlchemy(app)
manager = Manager(app)

@app.route('/')
def index():
    return render_template('base.html')

if __name__ == '__main__':
    manager.run()

from app import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    registration_date = db.Column(db.DateTime)

    messages_from = db.relationship('Message', primaryjoin='User.id==Message.sender_id')
    messages_to = db.relationship('Message', primaryjoin='User.id==Message.recipient_id')

    def __repr__(self):
        return (f'User(id={self.id}, username={self.username} '
                + f'registration_date={self.registration_date})')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.Text)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])
    message_date = db.Column(db.DateTime)

    def __repr__(self):
        return (f'Message(id={self.id}, text={self.text}, sender={self.sender.username} '
                + f'recipient={self.recipient.username}, message_date={self.message_date}')

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required, Length
from ..models import Message

class MessageForm(FlaskForm):
    message_text = StringField('', 
                               validators=[Required(), 
                                           Length(1, 1000)])
    submit = SubmitField('Send')

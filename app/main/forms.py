from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import Required, Length
from ..models import Message


class MessageForm(FlaskForm):
    message_field = TextAreaField(validators=[Length(1, 1000)],
                                  render_kw={'id': 'message-field-id',
                                             'cols': '38',
                                             'minlength': '1',
                                             'maxlength': '1000',
                                             'autofocus': 'autofocus',
                                             'placeholder': 'your message...'})


class UserSearchForm(FlaskForm):
    search_field = StringField(validators=[Length(1, 1000)],
                                render_kw={'id': 'user-search-id',
                                          'class': 'form-control',
                                          'type': 'search',
                                          'maxlength': '64',
                                          'placeholder': 'search...'})


class ChatSearchForm(FlaskForm):
    search_field = StringField(validators=[Length(1, 1000)],
                                render_kw={'id': 'chat-search-id',
                                          'class': 'form-control',
                                          'type': 'search',
                                          'maxlength': '64',
                                          'placeholder': 'search...'})

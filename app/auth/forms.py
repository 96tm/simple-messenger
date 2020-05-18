from flask_wtf import FlaskForm
from ..models import User
from wtforms import ValidationError
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import Email, Length, Required, Regexp, EqualTo


class LoginForm(FlaskForm):
    email = StringField('Email', 
                         validators=[Required(), Length(1, 64), Email()], 
                         render_kw={'placeholder': 'Email'})
    password = PasswordField('Password', 
                             validators=[Required(), ],
                             render_kw={'placeholder': 'Password'})
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                            validators=[Required(), 
                                        Length(1, 64),
                                        Regexp('^[A-Za-z0-9_. ]*$', 
                                               0,
                                               ('Username can only contain '
                                               + 'letters, digits, dots and '
                                               + 'underscores'))],
                            render_kw={'placeholder': 'Username'})
    email = StringField('Email',
                         validators=[Required(), Length(1, 64), Email()],
                         render_kw={'placeholder': 'Email'})
    password = PasswordField('Password', 
                             validators=[Required(),
                                         EqualTo('password_confirmation',
                                                 message=('Passwords '
                                                          + 'don\'t match'))],
                             render_kw={'placeholder': 'Password'})
    password_confirmation = PasswordField('Confirm password') 
    password_confirmation.validators=[Required()]
    password_confirmation.render_kw={'placeholder': 'Password'}
    submit = SubmitField('Sign Up')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('The email is already registered')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('The username is already taken')

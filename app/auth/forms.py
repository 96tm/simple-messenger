from ..models import User
from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import Email, EqualTo, Length, Regexp, Required


class LoginForm(FlaskForm):
    email = StringField('Email', 
                         validators=[Required(), Length(1, 64), Email()], 
                         render_kw={'class': 'form-control',
                                    'placeholder': 'Email'})
    password = PasswordField('Password', 
                             validators=[Required(), ],
                             render_kw={'class': 'form-control',
                                        'placeholder': 'Password',
                                        'required': 'required'})
    remember_me = BooleanField('Remember me',
                               render_kw={'class': 'custom-control-input'})
    
    submit_kw = {'class': 'btn btn-lg btn-primary btn-block text-uppercase'}
    submit = SubmitField('Log In',
                         render_kw=submit_kw)


class RegistrationForm(FlaskForm):
    regexp_message = ('Username can only contain letters, '
                      + 'digits, dots and underscores')
    username = StringField('Username', 
                            validators=[Required(), 
                                        Length(1, 64),
                                        Regexp('^[A-Za-z0-9_. ]*$', 
                                               0, regexp_message)],
                            render_kw={'class': 'form-control',
                                       'placeholder': 'Username',
                                       'required': 'required'})
    email = StringField('Email',
                         validators=[Required(), 
                                     Length(1, 64), 
                                     Email()],
                         render_kw={'class': 'form-control',
                                    'placeholder': 'Email'})
    
    password = PasswordField('Password', 
                             validators=[Required(),
                                         EqualTo('password_confirmation',
                                                 message=('Passwords '
                                                          + 'don\'t match'))],
                             render_kw={'class': 'form-control',
                                        'placeholder': 'Password',
                                        'required': 'required'})

    password_confirmation_kw = {'class': 'form-control',
                                'placeholder': 'Confirm password',
                                'required': 'required'}
    password_confirmation = PasswordField('Confirm password',
                                          validators=[Required()],
                                          render_kw=password_confirmation_kw)

    submit_kw = {'class': 'btn btn-lg btn-primary btn-block text-uppercase'}
    submit = SubmitField('Sign Up',
                         render_kw=submit_kw)

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('The email is already registered')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('The username is already taken')

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import Email, EqualTo, Length, Regexp, Required


class LoginForm(FlaskForm):
    email = StringField('Email', 
                         validators=[Required(), Length(5, 64), Email()], 
                         render_kw={'class': 'form-control',
                                    'placeholder': 'Email',
                                    'type': 'email',
                                    'minlength': '5',
                                    'maxlength': '64'})
    password = PasswordField('Password', 
                             validators=[Required(), Length(8, 64)],
                             render_kw={'class': 'form-control',
                                        'placeholder': 'Password',
                                        'required': 'required',
                                        'minlength': '8',
                                        'maxlength': '64'})
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
                                        Length(3, 64),
                                        Regexp('^[A-Za-z0-9_. ]*$', 
                                               0, regexp_message)],
                            render_kw={'class': 'form-control',
                                       'placeholder': 'Username',
                                       'required': 'required',
                                       'minlength': '3',
                                       'maxlength': '64'})
    email = StringField('Email',
                         validators=[Required(), 
                                     Length(5, 64), 
                                     Email()],
                         render_kw={'class': 'form-control',
                                    'placeholder': 'Email',
                                    'type': 'email',
                                    'minlength': '5',
                                    'maxlength': '64'})
    
    password = PasswordField('Password', 
                             validators=[Required(),
                                         Length(8, 64),
                                         EqualTo('password_confirmation',
                                                 message=('Passwords '
                                                          + 'don\'t match'))],
                             render_kw={'class': 'form-control',
                                        'placeholder': 'Password',
                                        'required': 'required',
                                        'minlength': '8',
                                        'maxlength': '64'})

    password_confirmation_kw = {'class': 'form-control',
                                'placeholder': 'Confirm password',
                                'required': 'required',
                                'minlength': '8',
                                'maxlength': '64'}
    password_confirmation = PasswordField('Confirm password',
                                          validators=[Required(),
                                                      Length(8, 64)],
                                          render_kw=password_confirmation_kw)

    submit_kw = {'class': 'btn btn-lg btn-primary btn-block text-uppercase'}
    submit = SubmitField('Sign Up',
                         render_kw=submit_kw)
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import Email, Length, Required

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()], render_kw={'placeholder': 'Email'})
    password = PasswordField('Password', 
                             validators=[Required(), ],
                             render_kw={'placeholder': 'Password'})
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log In')

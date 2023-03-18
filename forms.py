"""WTForms for Pawprint"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, URLField
from wtforms.validators import DataRequired, Email, Length, Optional


class SignUpForm(FlaskForm):
    """Form for adding a new user"""

    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('(Optional) Last Name', validators=[Optional()])
    location = StringField('(Optional) Location', validators=[Optional()])
    profile_picture_url = URLField('(Optional) Profile Picture URL', validators=[Optional()])

class LoginForm(FlaskForm):
    """Form for user login"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
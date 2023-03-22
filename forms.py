"""WTForms for Pawprint"""

from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, URLField, RadioField, SelectField, IntegerField
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

class EditUserForm(FlaskForm):
    """For for editing user profile"""

    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('(Optional) Last Name', validators=[Optional()])
    location = StringField('(Optional) Location', validators=[Optional()])
    profile_picture_url = URLField('(Optional) Profile Picture URL', validators=[Optional()])

class PetSearchForm(FlaskForm):
    """Form for searching for pets."""

    type = StringField('Type (e.g. "dog" or "cat")')
    breed = StringField('Breed(s) (e.g. "pug" or "pug,samoyed")')
    size = StringField('Size(s) (e.g. "small" or "large,xlarge")')
    gender = StringField('Gender (e.g. "male" or "female")')
    age = StringField('Age(s) (e.g. "baby" or "young,adult")')
    color = StringField('Color (e.g. "black" or "white")')
    status = StringField('Status (e.g. "adoptable" or "found")')
    name = StringField('Name (e.g. "Fred" or "Spark")')
    location = StringField('Location ("[City], [State]"; or "[PostalCode]")')

class OrganizationSearchForm(FlaskForm):
    """Form for searching for animal welfare organizations."""

    name = StringField('Name (e.g. "Sanctuary" or "Rescue")')
    location = StringField('Location ("[City], [State]"; or "[PostalCode]")')
    distance = IntegerField('Maximum distance (in number of miles) from Location (Default is 100)')
    state = StringField('State (e.g. "CA" or "NY")')
    country = StringField('Country (e.g. "US" or "CA")')

# class SearchForm(FlaskForm):
#     """Form for searching for pets or organizations"""

#     search_target = RadioField('Search for: ',
#                                choices=[("pets", "Pets"),
#                                         ("organizations", "Animal Welfare Organizations")],
#                                         validators=[DataRequired()])
    
# class PetSearchForm(Form):
#     """
#     Subform specific to pet searches.
    
#     Inherits WTForms base Form class to disable CSRF because
#     this subform is never used by itself.
#     """

#     name = StringField('Name')
#     type = StringField('Type') # specify further later
#     breed = StringField('Breed')
#     location = StringField('Location') # specify further later

# class OrganizationSearchForm(Form):
#     """
#     Subform specific to organization searches.
    
#     Inherits WTForms base Form class to disable CSRF because
#     this subform is never used by itself.
#     """

#     name = StringField('Organization Name')
#     location = StringField('Location') #specify further later
#     state = StringField('State')
#     country = StringField('Country')


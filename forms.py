from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, FileField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    profile_photo = FileField('Profile Photo')

class TestTypeForm(FlaskForm):
    test_type = StringField('Test Type', validators=[DataRequired(), Length(min=2, max=64)])
    language = StringField('Language', validators=[DataRequired(), Length(min=2, max=64)])
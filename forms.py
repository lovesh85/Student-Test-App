from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, FileField, TextAreaField, SelectField
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
    name = StringField('Test Type', validators=[DataRequired(), Length(min=2, max=64)])
    language = StringField('Language', validators=[DataRequired(), Length(min=2, max=64)])

class TestMasterForm(FlaskForm):
    test_type = SelectField('Test Type', coerce=int, validators=[DataRequired()])
    question = TextAreaField('Question', validators=[DataRequired()])
    question_image = FileField('Question Image')
    answer_a = TextAreaField('Answer (A)', validators=[DataRequired()])
    answer_b = TextAreaField('Answer (B)', validators=[DataRequired()])
    answer_c = TextAreaField('Answer (C)', validators=[DataRequired()])
    answer_d = TextAreaField('Answer (D)', validators=[DataRequired()])
    correct_answer = SelectField('Correct Answer', choices=[
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')
    ], validators=[DataRequired()])

class AllocateTestForm(FlaskForm):
    user = SelectField('User', coerce=int, validators=[DataRequired()])
    test_type = SelectField('Test Type', coerce=int, validators=[DataRequired()])

class StartTestForm(FlaskForm):
    test_type = SelectField('Test Type', coerce=int, validators=[DataRequired()])
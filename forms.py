"""
WTForms definitions for authentication and profile actions.
Enforces CSRF and input validation rules.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, URL


class RegistrationForm(FlaskForm):
    """Student registration form."""
    display_name = StringField(
        "Display Name",
        validators=[
            DataRequired(message="Please enter your full name."),
            Length(min=2, max=100, message="Display name must be between 2 and 100 characters."),
        ],
    )
    email = StringField(
        "College Email Address",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address."),
            Length(max=255, message="Email must be less than 255 characters."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please choose a password."),
            Length(min=8, message="Password must be at least 8 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter your password."),
        ],
    )
    submit = SubmitField("Log In")

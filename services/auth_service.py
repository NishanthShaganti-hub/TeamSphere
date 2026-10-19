"""
Authentication and registration business logic.
Enforces security rules, normalization, and role constraints.
"""

from typing import Optional, Tuple
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import User
from utils.validators import normalize_email, validate_college_email


def register_student(
    display_name: str,
    email: str,
    password: str,
    allowed_domain: str = "",
) -> Tuple[Optional[User], Optional[str]]:
    """
    Register a new student account.
    CRITICAL SECURITY RULE: Public registration ALWAYS assigns the 'student' role.
    """
    name = (display_name or "").strip()
    norm_email = normalize_email(email)

    if not name or len(name) < 2 or len(name) > 100:
        return None, "Display name must be between 2 and 100 characters."

    if not norm_email or "@" not in norm_email:
        return None, "Please provide a valid email address."

    if not validate_college_email(norm_email, allowed_domain):
        return None, f"Registration is restricted to @{allowed_domain} email addresses."

    if not password or len(password) < 8:
        return None, "Password must be at least 8 characters long."

    # Check for existing email in application logic
    existing_user = User.query.filter_by(email=norm_email).first()
    if existing_user:
        return None, "An account with this email address already exists."

    try:
        new_student = User(
            display_name=name,
            email=norm_email,
            role="student",  # Hardcoded student role
        )
        new_student.set_password(password)

        db.session.add(new_student)
        db.session.commit()
        return new_student, None
    except IntegrityError:
        db.session.rollback()
        return None, "An account with this email address already exists."
    except Exception as e:
        db.session.rollback()
        return None, "A server error occurred during registration. Please try again."


def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Verify user credentials.
    Returns the User on success, or None on invalid credentials.
    """
    if not email or not password:
        return None

    norm_email = normalize_email(email)
    user = User.query.filter_by(email=norm_email).first()

    if user and user.check_password(password):
        return user

    return None

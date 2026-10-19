"""
Stage 3 Tests: Student registration, login, logout, sessions, role assignment,
and open redirect security.
"""

from models import User
from extensions import db
from utils.validators import is_safe_url


def test_register_student_success(client, app):
    """Verify that a student can register and is always given role='student'."""
    response = client.post(
        "/register",
        data={
            "display_name": "Bob Martin",
            "email": "BOB.MARTIN@COLLEGE.EDU",  # uppercase test
            "password": "supersecretpassword123",
            "confirm_password": "supersecretpassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Welcome to TeamSphere" in html or "Dashboard" in html

    with app.app_context():
        user = User.query.filter_by(email="bob.martin@college.edu").first()
        assert user is not None
        assert user.display_name == "Bob Martin"
        # Email stored lowercase
        assert user.email == "bob.martin@college.edu"
        # Role must strictly be 'student'
        assert user.role == "student"
        # Password must be hashed with Werkzeug, never plain text
        assert user.password_hash != "supersecretpassword123"
        assert user.check_password("supersecretpassword123") is True


def test_register_duplicate_email_fails(client, app):
    """Verify duplicate email registration is rejected with friendly message."""
    with app.app_context():
        u = User(display_name="Existing User", email="existing@college.edu")
        u.set_password("existingpass123")
        db.session.add(u)
        db.session.commit()

    response = client.post(
        "/register",
        data={
            "display_name": "Another User",
            "email": "existing@college.edu",
            "password": "anotherpassword123",
            "confirm_password": "anotherpassword123",
        },
    )
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "An account with this email address already exists." in html


def test_register_role_injection_prevented(client, app):
    """Verify malicious client cannot inject role='admin' or role='faculty' during registration."""
    client.post(
        "/register",
        data={
            "display_name": "Hacker Jane",
            "email": "jane@college.edu",
            "password": "secretpassword123",
            "confirm_password": "secretpassword123",
            "role": "admin",  # Attacker attempt
        },
    )

    with app.app_context():
        user = User.query.filter_by(email="jane@college.edu").first()
        assert user is not None
        assert user.role == "student", "Registration must ignore submitted role and strictly set 'student'"


def test_login_success(client, app):
    """Verify student can log in with valid credentials."""
    with app.app_context():
        u = User(display_name="Login Student", email="loginstudent@college.edu")
        u.set_password("validpassword123")
        db.session.add(u)
        db.session.commit()

    response = client.post(
        "/login",
        data={
            "email": "loginstudent@college.edu",
            "password": "validpassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Welcome back, Login Student!" in html


def test_login_invalid_password_returns_generic_error(client, app):
    """Verify incorrect password returns generic error message without leaking existence."""
    with app.app_context():
        u = User(display_name="Target Student", email="target@college.edu")
        u.set_password("correctpassword123")
        db.session.add(u)
        db.session.commit()

    response = client.post(
        "/login",
        data={
            "email": "target@college.edu",
            "password": "wrongpassword999",
        },
    )
    assert response.status_code == 401
    html = response.get_data(as_text=True)
    assert "Invalid email or password." in html


def test_login_unknown_email_returns_generic_error(client):
    """Verify non-existent email returns exact same generic error message."""
    response = client.post(
        "/login",
        data={
            "email": "nonexistent@college.edu",
            "password": "anypassword123",
        },
    )
    assert response.status_code == 401
    html = response.get_data(as_text=True)
    assert "Invalid email or password." in html


def test_pre_login_session_data_cleared(client, app):
    """Verify pre-login session data is cleared upon successful login."""
    with app.app_context():
        u = User(display_name="Session Student", email="session@college.edu")
        u.set_password("sessionpass123")
        db.session.add(u)
        db.session.commit()

    # Set some dummy pre-login session data
    with client.session_transaction() as sess:
        sess["untrusted_prelogin_key"] = "attacker_value"

    # Log in
    client.post(
        "/login",
        data={
            "email": "session@college.edu",
            "password": "sessionpass123",
        },
    )

    with client.session_transaction() as sess:
        assert "untrusted_prelogin_key" not in sess, "Pre-login session data must be wiped upon login"


def test_logout(client, app):
    """Verify logout clears authentication state."""
    with app.app_context():
        u = User(display_name="Logout Student", email="logout@college.edu")
        u.set_password("logoutpass123")
        db.session.add(u)
        db.session.commit()

    # Log in
    client.post(
        "/login",
        data={
            "email": "logout@college.edu",
            "password": "logoutpass123",
        },
    )

    # Log out
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "You have been signed out." in html

    # Subsequent request to protected dashboard redirects to login
    dash_response = client.get("/dashboard")
    assert dash_response.status_code == 302
    assert "/login" in dash_response.headers["Location"]


def test_safe_redirect_validation():
    """Verify is_safe_url blocks open redirects and tricky bypass attempts."""
    # Safe relative paths
    assert is_safe_url("/projects") is True
    assert is_safe_url("/team-finder") is True
    assert is_safe_url("/dashboard?tab=sent") is True

    # Unsafe / open redirect attempts
    assert is_safe_url("https://evil.example.com") is False
    assert is_safe_url("http://evil.example.com") is False
    assert is_safe_url("//evil.example.com") is False
    assert is_safe_url("///evil.example.com") is False
    assert is_safe_url("/\\evil.example.com") is False
    assert is_safe_url("/\\\\evil.example.com") is False
    assert is_safe_url("javascript:alert(1)") is False
    assert is_safe_url("") is False
    assert is_safe_url(None) is False


def test_login_safe_redirect(client, app):
    """Verify that login redirects to safe relative URLs but drops external open redirects."""
    with app.app_context():
        u = User(display_name="Redirect Student", email="redirect@college.edu")
        u.set_password("redirectpass123")
        db.session.add(u)
        db.session.commit()

    # 1. Safe relative next parameter
    res1 = client.post(
        "/login?next=/projects",
        data={
            "email": "redirect@college.edu",
            "password": "redirectpass123",
        },
    )
    assert res1.status_code == 302
    assert res1.headers["Location"] == "/projects"

    # 2. Malicious open redirect attempt must redirect to /dashboard instead
    res2 = client.post(
        "/login?next=https://evil.example.com",
        data={
            "email": "redirect@college.edu",
            "password": "redirectpass123",
        },
    )
    assert res2.status_code == 302
    assert "/dashboard" in res2.headers["Location"]

    # 3. Protocol-relative bypass attempt
    res3 = client.post(
        "/login?next=//evil.example.com",
        data={
            "email": "redirect@college.edu",
            "password": "redirectpass123",
        },
    )
    assert res3.status_code == 302
    assert "/dashboard" in res3.headers["Location"]

"""
Tests for Student Profile editing, database persistence, and privacy protection.
"""

from models import User, Skill, Interest
from extensions import db


def test_edit_profile_saves_to_database(client, app):
    """Verify that editing a profile persists bio, skills, and department to the database."""
    with app.app_context():
        user = User(
            display_name="Alice Student",
            email="alice.student@college.edu",
            department="Department of Information Technology",
            year_of_study=2,
        )
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    # Log in
    client.post(
        "/login",
        data={"email": "alice.student@college.edu", "password": "Password123!"},
    )

    # Submit profile edit
    response = client.post(
        "/profile/edit",
        data={
            "display_name": "Alice S. Senior",
            "department": "Department of Information Technology",
            "year_of_study": "4",
            "bio": "Passionate about full-stack web and database design with SQLite.",
            "skills": "python, flask, sql",
            "interests": "cloud computing, ai ethics",
            "profile_image_url": "https://example.com/avatar.jpg",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Check updated content is visible
    assert "Alice S. Senior" in html
    assert "Passionate about full-stack web and database design with SQLite." in html
    assert "python" in html
    assert "sql" in html

    # Verify directly from database
    with app.app_context():
        updated_user = db.session.get(User, user_id)
        assert updated_user.display_name == "Alice S. Senior"
        assert updated_user.year_of_study == 4
        assert updated_user.bio == "Passionate about full-stack web and database design with SQLite."
        assert updated_user.profile_image_url == "https://example.com/avatar.jpg"
        user_skills = [s.name for s in updated_user.skills]
        assert "python" in user_skills
        assert "flask" in user_skills
        assert "sql" in user_skills
        user_interests = [i.name for i in updated_user.interests]
        assert "cloud computing" in user_interests


def test_profile_privacy_never_exposes_email_or_password_hash(client, app):
    """Verify other students' email addresses and password hashes are never exposed."""
    with app.app_context():
        secret_user = User(
            display_name="Private Student",
            email="secret.personal@college.edu",
            bio="My bio is public.",
        )
        secret_user.set_password("SecretPassword999!")
        db.session.add(secret_user)
        db.session.commit()
        user_id = secret_user.id
        stored_hash = secret_user.password_hash

    # View public profile
    response = client.get(f"/profile/{user_id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Bio and name are public
    assert "Private Student" in html
    assert "My bio is public." in html

    # Email and password hash MUST NOT be in the HTML
    assert "secret.personal@college.edu" not in html
    assert stored_hash not in html
    assert "Contact happens securely through team-up requests. Email address is private." in html


def test_unauthenticated_cannot_edit_profile(client):
    """Verify logged-out user is redirected to login when trying to edit profile."""
    response = client.get("/profile/edit")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

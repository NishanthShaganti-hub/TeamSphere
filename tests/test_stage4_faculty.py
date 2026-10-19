"""
Tests for Faculty Role, CLI creation, and Verified Hackathon/Project badges.
"""

from models import User, Project
from extensions import db


def test_create_faculty_command(app):
    """Verify that create-faculty CLI command creates a verified faculty account."""
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "create-faculty",
            "--name", "Dr. Rajesh Sharma",
            "--email", "rajesh.sharma@college.edu",
            "--dept", "Department of Information Technology",
            "--password", "FacultyPass123!",
        ]
    )

    assert result.exit_code == 0
    assert "Success! Faculty account" in result.output

    with app.app_context():
        faculty = User.query.filter_by(email="rajesh.sharma@college.edu").first()
        assert faculty is not None
        assert faculty.display_name == "Dr. Rajesh Sharma"
        assert faculty.role == "faculty"
        assert faculty.check_password("FacultyPass123!") is True


def test_faculty_project_displays_verified_badge(client, app):
    """Verify projects posted by faculty display the Faculty Verified badge."""
    with app.app_context():
        prof = User(
            display_name="Elena Vance",
            email="elena.vance@college.edu",
            role="faculty",
            department="Department of Information Technology",
        )
        prof.set_password("FacultyPass123!")
        db.session.add(prof)
        db.session.commit()

        hackathon = Project(
            owner_id=prof.id,
            title="Annual IT Department Hackathon 2026",
            short_description="Official department hackathon challenge on sustainable computing.",
            full_description="All IT students are invited to register teams of 2 to 4 members...",
            category="hackathon",
            status="looking_for_teammates",
        )
        db.session.add(hackathon)
        db.session.commit()
        project_id = hackathon.id

    # 1. Check Projects Directory
    res_list = client.get("/projects")
    assert res_list.status_code == 200
    html_list = res_list.get_data(as_text=True)
    assert "Annual IT Department Hackathon 2026" in html_list
    assert "Faculty Verified" in html_list
    assert "Prof. Elena Vance" in html_list

    # 2. Check Project Detail Page
    res_detail = client.get(f"/projects/{project_id}")
    assert res_detail.status_code == 200
    html_detail = res_detail.get_data(as_text=True)
    assert "Faculty / Department Verified" in html_detail
    assert "Faculty Mentor / Lead" in html_detail

    # 3. Check Faculty Filter in Browse Projects
    res_faculty_filter = client.get("/projects?faculty=true")
    assert res_faculty_filter.status_code == 200
    html_filter = res_faculty_filter.get_data(as_text=True)
    assert "Annual IT Department Hackathon 2026" in html_filter


def test_public_registration_cannot_create_faculty(client, app):
    """Re-verify that public registration form always forces role='student'."""
    client.post(
        "/register",
        data={
            "display_name": "Pretending Professor",
            "email": "pretend@college.edu",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "faculty",  # Injection attempt
        },
    )

    with app.app_context():
        user = User.query.filter_by(email="pretend@college.edu").first()
        assert user is not None
        assert user.role == "student", "Role must be 'student' on public registration!"

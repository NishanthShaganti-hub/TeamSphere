"""
Stage 2 Tests: Shared layout, navigation, landing page, static assets, and error pages.
"""

from models import User, Project, Skill
from extensions import db


def test_landing_page_renders_html(client):
    """Verify landing page renders successfully with design system landmarks."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Check semantic landmarks and content
    assert "<!DOCTYPE html>" in html
    assert "TeamSphere" in html
    assert '<span class="brand-mark" aria-hidden="true">TS</span>' in html
    assert ">TF</span>" not in html
    assert "Find teammates." in html
    assert "Build something together." in html
    assert "A simple way to get started" in html
    assert "Recent projects" in html
    assert "Around the department" not in html
    assert 'name="csrf-token"' in html
    assert 'href="/static/css/style.css"' in html
    assert 'src="/static/js/main.js"' in html


def test_static_css_served(client):
    """Verify custom CSS stylesheet is served properly."""
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    css = response.get_data(as_text=True)
    assert "--primary: #3b43b5;" in css
    assert "--bg: #f4f5fb;" in css
    assert ".navbar-wrapper" in css
    assert ".project-card-looking_for_teammates" in css
    assert ".category-hackathon" in css
    assert ".feature-card:nth-child(4)" in css
    assert ".avatar-tint-5" in css
    assert ".tag.t5" in css


def test_skill_color_filter_returns_stable_palette_index(app):
    """Verify skill tags map consistently into the six available palette colors."""
    skill_color = app.jinja_env.filters["skill_color"]
    assert skill_color("python") == skill_color("python")
    assert 0 <= skill_color("python") <= 5


def test_static_js_served(client):
    """Verify vanilla JS script is served properly."""
    response = client.get("/static/js/main.js")
    assert response.status_code == 200
    js = response.get_data(as_text=True)
    assert "showToast" in js
    assert "openModal" in js
    assert "fetchWithCsrf" in js
    assert "initSearchShortcut" in js


def test_404_custom_error_page(client):
    """Verify nonexistent routes render the custom 404 error page."""
    response = client.get("/definitely-not-a-real-page-12345")
    assert response.status_code == 404
    html = response.get_data(as_text=True)
    assert "404" in html
    assert "Page Not Found" in html
    assert "Back to Home" in html


def test_landing_page_shows_recent_projects(client, app):
    """Verify that recent active projects appear dynamically on the landing page."""
    with app.app_context():
        # Create a sample student and project
        student = User(display_name="Sarah Developer", email="sarah@college.edu", password_hash="dummy")
        db.session.add(student)
        db.session.commit()

        skill = Skill(name="python")
        db.session.add(skill)
        db.session.commit()

        project = Project(
            owner_id=student.id,
            title="Smart Campus Navigator",
            short_description="An interactive map helping freshmen find classrooms.",
            full_description="Longer description here...",
            category="hackathon",
            status="looking_for_teammates",
        )
        project.skills.append(skill)
        db.session.add(project)
        db.session.commit()

    # Request landing page
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Smart Campus Navigator" in html
    assert "Sarah Developer" in html
    assert "python" in html
    assert "Around the department" in html
    assert "projects looking for teammates" in html
    assert "student collaborators" in html
    assert "completed projects in the archive" in html
    assert '<span class="hero-stat-number">1</span>' in html


def test_projects_are_added_by_authenticated_owners(client):
    """Verify the project board starts empty and accepts owner-submitted listings."""
    response = client.get("/projects")
    assert response.status_code == 200
    assert "No projects posted yet." in response.get_data(as_text=True)

    registration = client.post(
        "/register",
        data={
            "display_name": "Project Owner",
            "email": "owner@college.edu",
            "password": "ownerpassword123",
            "confirm_password": "ownerpassword123",
        },
    )
    assert registration.status_code == 302

    response = client.post(
        "/projects/new",
        data={
            "title": "Student-submitted project",
            "short_description": "A real project shared by its owner.",
            "full_description": "Project details written by the authenticated owner.",
            "category": "academic",
            "status": "looking_for_teammates",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Student-submitted project" in response.get_data(as_text=True)


def test_dashboard_shows_profile_progress_for_new_students(client, app):
    """New students see a clear profile-completion next step on their dashboard."""
    with app.app_context():
        student = User(
            display_name="New Student",
            email="new-student@college.edu",
        )
        student.set_password("studentpassword123")
        db.session.add(student)
        db.session.commit()

    client.post(
        "/login",
        data={"email": "new-student@college.edu", "password": "studentpassword123"},
    )
    response = client.get("/dashboard")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Make it easier for teammates to find you" in html
    assert 'aria-valuenow="0"' in html
    assert "Update your profile" in html
    assert "My builds" in html

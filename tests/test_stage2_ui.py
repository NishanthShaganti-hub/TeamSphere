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
    assert "Find teammates. Build something together." in html
    assert "How TeamSphere Works" in html
    assert "Recent Projects" in html
    assert 'name="csrf-token"' in html
    assert 'href="/static/css/style.css"' in html
    assert 'src="/static/js/main.js"' in html


def test_static_css_served(client):
    """Verify custom CSS stylesheet is served properly."""
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    css = response.get_data(as_text=True)
    assert "--primary: #2f3e4e;" in css
    assert "--bg: #f6f7f8;" in css
    assert ".navbar-wrapper" in css


def test_static_js_served(client):
    """Verify vanilla JS script is served properly."""
    response = client.get("/static/js/main.js")
    assert response.status_code == 200
    js = response.get_data(as_text=True)
    assert "showToast" in js
    assert "openModal" in js
    assert "fetchWithCsrf" in js


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

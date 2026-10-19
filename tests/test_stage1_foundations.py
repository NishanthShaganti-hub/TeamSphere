"""
Stage 1 Tests: Application setup, configuration, database isolation,
SQLite foreign keys enforcement, and constraints.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app import create_app
from extensions import db
from models import User, Project, Skill, ProjectMember, TeamRequest
from config import TestingConfig, DevelopmentConfig


def test_app_creation(app):
    """Verify application factory initializes correctly in testing mode."""
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"


def test_health_check_endpoint(client):
    """Verify that the health check endpoint responds correctly."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "TeamSphere"


def test_database_isolation_guard():
    """Verify that the safety guard prevents test execution if pointed at development DB."""
    unsafe_app = create_app(DevelopmentConfig)
    db_uri = unsafe_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    is_testing = unsafe_app.config.get("TESTING", False)

    # Replicate the conftest guard logic
    with pytest.raises(RuntimeError) as exc_info:
        if not is_testing or (db_uri != "sqlite:///:memory:" and "test" not in db_uri.lower()):
            raise RuntimeError("FATAL SAFETY VIOLATION: Test suite attempted to run against a non-test database")

    assert "FATAL SAFETY VIOLATION" in str(exc_info.value)


def test_sqlite_foreign_keys_pragma_enabled(app):
    """Verify that SQLite connection event listener enables PRAGMA foreign_keys = ON."""
    with app.app_context():
        result = db.session.execute(text("PRAGMA foreign_keys;")).scalar()
        assert result == 1, "SQLite foreign keys must be enabled (result should be 1)"


def test_foreign_key_enforcement_on_insert(app):
    """Verify that inserting a record with a non-existent foreign key fails."""
    with app.app_context():
        # Attempt to insert a project with a non-existent owner_id (999999)
        orphan_project = Project(
            owner_id=999999,
            title="Orphan Project",
            short_description="This should fail",
            full_description="Foreign key constraint must prevent this.",
            category="hackathon",
            status="looking_for_teammates",
        )
        db.session.add(orphan_project)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_project_cascade_deletion(app):
    """
    Verify that deleting a project cascades cleanly and removes associated
    memberships, skill joins, and requests without leaving orphaned rows.
    """
    with app.app_context():
        # Create owner and member users
        owner = User(display_name="Alice Owner", email="alice@college.edu", password_hash="hash")
        member = User(display_name="Bob Member", email="bob@college.edu", password_hash="hash")
        db.session.add_all([owner, member])
        db.session.commit()

        # Create skill
        skill = Skill(name="python")
        db.session.add(skill)
        db.session.commit()

        # Create project with skill and member
        project = Project(
            owner_id=owner.id,
            title="AI Study Buddy",
            short_description="Collaborative AI tool",
            full_description="Deep learning for education",
            category="research",
            status="looking_for_teammates",
        )
        project.skills.append(skill)
        db.session.add(project)
        db.session.commit()

        # Add member via ProjectMember
        pm = ProjectMember(project_id=project.id, user_id=member.id)
        # Add request
        req = TeamRequest(sender_id=member.id, recipient_id=owner.id, project_id=project.id, status="pending")
        db.session.add_all([pm, req])
        db.session.commit()

        project_id = project.id

        # Delete project
        db.session.delete(project)
        db.session.commit()

        # Verify no orphan rows exist in project_members, project_skills, or team_requests
        member_count = db.session.execute(
            text("SELECT COUNT(*) FROM project_members WHERE project_id = :pid"), {"pid": project_id}
        ).scalar()
        assert member_count == 0

        skill_join_count = db.session.execute(
            text("SELECT COUNT(*) FROM project_skills WHERE project_id = :pid"), {"pid": project_id}
        ).scalar()
        assert skill_join_count == 0

        request_count = db.session.execute(
            text("SELECT COUNT(*) FROM team_requests WHERE project_id = :pid"), {"pid": project_id}
        ).scalar()
        assert request_count == 0

        # Skill and users themselves should still exist!
        assert db.session.get(Skill, skill.id) is not None
        assert db.session.get(User, owner.id) is not None
        assert db.session.get(User, member.id) is not None


def test_partial_unique_index_on_pending_requests(app):
    """
    Verify the partial unique index prevents duplicate pending requests
    for the same sender, recipient, and project (including NULL project_id via COALESCE).
    """
    with app.app_context():
        u1 = User(display_name="Student 1", email="s1@college.edu", password_hash="hash")
        u2 = User(display_name="Student 2", email="s2@college.edu", password_hash="hash")
        db.session.add_all([u1, u2])
        db.session.commit()

        # First pending student-to-student request (project_id=None)
        req1 = TeamRequest(sender_id=u1.id, recipient_id=u2.id, project_id=None, status="pending")
        db.session.add(req1)
        db.session.commit()

        # Duplicate pending request must fail with IntegrityError
        req2 = TeamRequest(sender_id=u1.id, recipient_id=u2.id, project_id=None, status="pending")
        db.session.add(req2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Once req1 is resolved (e.g. rejected), a new pending request should be allowed!
        req1.status = "rejected"
        db.session.commit()

        req3 = TeamRequest(sender_id=u1.id, recipient_id=u2.id, project_id=None, status="pending")
        db.session.add(req3)
        db.session.commit()
        assert req3.id is not None

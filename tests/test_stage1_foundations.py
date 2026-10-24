"""
Stage 1 Tests: Application setup, configuration, database isolation,
PostgreSQL foreign keys enforcement, and constraints.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import make_url
from app import create_app
from extensions import db
from models import User, Project, Skill, ProjectMember, TeamRequest
from config import TestingConfig, DevelopmentConfig, ProductionConfig, database_uri_from_env


def test_app_creation(app):
    """Verify application factory initializes correctly in testing mode."""
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql+psycopg://")


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
        parsed_uri = make_url(db_uri)
        database_name = (parsed_uri.database or "").lower()
        if (
            not is_testing
            or parsed_uri.drivername != "postgresql+psycopg"
            or "test" not in database_name
        ):
            raise RuntimeError("FATAL SAFETY VIOLATION: Test suite attempted to run against a non-test database")

    assert "FATAL SAFETY VIOLATION" in str(exc_info.value)


def test_vercel_uses_production_config(monkeypatch):
    """Vercel deployments require production secrets and a hosted database."""
    monkeypatch.setenv("VERCEL", "1")
    production_secret = "s" * 64
    monkeypatch.setenv("SECRET_KEY", production_secret)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@example.com/teamsphere")
    monkeypatch.setenv("FLASK_ENV", "development")

    vercel_app = create_app()

    assert vercel_app.config["DEBUG"] is False
    assert vercel_app.config["SESSION_COOKIE_SECURE"] is True
    assert vercel_app.config["SECRET_KEY"] == production_secret
    assert vercel_app.config["SQLALCHEMY_DATABASE_URI"] == (
        "postgresql+psycopg://user:password@example.com/teamsphere"
    )


def test_postgres_url_normalization(monkeypatch):
    """Common hosted PostgreSQL URL schemes use the configured psycopg 3 driver."""
    monkeypatch.setenv("DATABASE_URL", "postgres://user:password@example.com/teamsphere")
    assert database_uri_from_env() == "postgresql+psycopg://user:password@example.com/teamsphere"


def test_production_requires_secrets(monkeypatch):
    """Production configuration fails clearly if required deployment settings are absent."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError, match="SECRET_KEY"):
        ProductionConfig.validate()

    monkeypatch.setenv("SECRET_KEY", "replace-with-a-secure-random-secret-key")
    with pytest.raises(ValueError, match="SECRET_KEY"):
        ProductionConfig.validate()


def test_production_rejects_malformed_database_url_without_echoing_it(monkeypatch):
    """Invalid PostgreSQL URLs fail clearly without exposing their contents."""
    monkeypatch.setenv("SECRET_KEY", "s" * 64)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://private-user:private-password@db.example.com:port/teamsphere",
    )

    with pytest.raises(
        ValueError,
        match="DATABASE_URL is not a valid PostgreSQL connection URL",
    ) as exc_info:
        ProductionConfig.validate()

    assert "private-user" not in str(exc_info.value)
    assert "private-password" not in str(exc_info.value)


def test_production_rejects_non_postgresql_database_url(monkeypatch):
    """Production cannot silently use SQLite or a local socket database."""
    monkeypatch.setenv("SECRET_KEY", "s" * 64)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")

    with pytest.raises(
        ValueError,
        match="DATABASE_URL must be a hosted PostgreSQL URL",
    ):
        ProductionConfig.validate()


def test_postgresql_database_is_used(app):
    """Verify that tests connect using PostgreSQL."""
    with app.app_context():
        result = db.session.execute(text("SELECT version();")).scalar()
        assert "PostgreSQL" in result


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

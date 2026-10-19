"""
Pytest configuration and fixtures for TeamSphere.
Enforces strict test database isolation so the development database is never touched.
"""

import pytest
from app import create_app
from extensions import db
from config import TestingConfig


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask application instance for testing."""
    test_app = create_app(TestingConfig)

    # SAFETY GUARD: Ensure tests never target the development database
    db_uri = test_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    is_testing = test_app.config.get("TESTING", False)

    if not is_testing or (db_uri != "sqlite:///:memory:" and "test" not in db_uri.lower()):
        raise RuntimeError(
            f"FATAL SAFETY VIOLATION: Test suite attempted to run against a non-test database: '{db_uri}'. "
            "Tests must strictly use an in-memory SQLite database ('sqlite:///:memory:') or a dedicated test database."
        )

    return test_app


@pytest.fixture(autouse=True)
def db_session(app):
    """
    Provide clean database tables for each test.
    Creates schema before the test and drops all tables after.
    """
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for sending HTTP requests to the application."""
    return app.test_client()

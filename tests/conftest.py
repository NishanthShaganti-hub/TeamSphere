"""
Pytest configuration and fixtures for TeamSphere.
Enforces strict test database isolation so the development database is never touched.
"""

import pytest
from sqlalchemy.engine import make_url
from app import create_app
from extensions import db
from config import TestingConfig


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask application instance for testing."""
    test_app = create_app(TestingConfig)

    # SAFETY GUARD: Tests must use a dedicated PostgreSQL test database.
    db_uri = test_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    is_testing = test_app.config.get("TESTING", False)
    parsed_uri = make_url(db_uri)
    database_name = (parsed_uri.database or "").lower()

    if (
        not is_testing
        or parsed_uri.drivername != "postgresql+psycopg"
        or "test" not in database_name
    ):
        raise RuntimeError(
            f"FATAL SAFETY VIOLATION: Test suite attempted to run against a non-test database: '{db_uri}'. "
            "Set TEST_DATABASE_URL to a dedicated PostgreSQL database with 'test' in its name."
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

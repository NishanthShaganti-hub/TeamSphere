import os
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

# Load environment variables from .env file if present
load_dotenv(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".env"))


def normalize_database_uri(uri):
    """Normalize PostgreSQL URLs for the psycopg 3 SQLAlchemy driver."""
    if uri and uri.startswith("postgres://"):
        return "postgresql+psycopg://" + uri[len("postgres://"):]
    if uri and uri.startswith("postgresql://"):
        return "postgresql+psycopg://" + uri[len("postgresql://"):]
    return uri


def database_uri_from_env():
    """Return the configured application database URL."""
    return normalize_database_uri(os.environ.get("DATABASE_URL"))


class Config:
    """Base configuration shared across environments."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "teamsphere-dev-insecure-secret-key-39184")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security: Session cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Email domain restriction (empty means open to any valid email address)
    ALLOWED_EMAIL_DOMAIN = os.environ.get("ALLOWED_EMAIL_DOMAIN", "").strip().lower()

    # Flask-Limiter rate limiting
    RATELIMIT_DEFAULT = "200 per day; 50 per hour"
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_STRATEGY = "moving-window"

    # Pagination settings
    ITEMS_PER_PAGE = 12


class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = database_uri_from_env() or "postgresql+psycopg:///teamsphere"


class TestingConfig(Config):
    """Testing configuration isolated from development database."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = normalize_database_uri(
        os.environ.get("TEST_DATABASE_URL")
    ) or "postgresql+psycopg:///teamsphere_test"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = "test-secret-key-never-used-in-production"
    # Ensure secure cookie is disabled during local test runs
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration with strict security requirements."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        """Validate required production secrets and PostgreSQL connection settings."""
        secret = os.environ.get("SECRET_KEY", "").strip()
        if (
            not secret
            or len(secret) < 32
            or "dev-insecure" in secret
            or secret == "replace-with-a-secure-random-secret-key"
        ):
            raise ValueError(
                "SECRET_KEY must be set to a random value of at least 32 characters in production."
            )

        database_uri = database_uri_from_env()
        if not database_uri:
            raise ValueError("DATABASE_URL must be set to a hosted PostgreSQL database in production.")
        try:
            parsed_uri = make_url(database_uri)
        except (ArgumentError, ValueError):
            raise ValueError(
                "DATABASE_URL is not a valid PostgreSQL connection URL. Check its format and URL-encode special characters in credentials."
            ) from None

        if (
            parsed_uri.drivername != "postgresql+psycopg"
            or not parsed_uri.host
            or not parsed_uri.database
        ):
            raise ValueError(
                "DATABASE_URL must be a hosted PostgreSQL URL with a hostname and database name."
            )

        cls.SECRET_KEY = secret
        cls.SQLALCHEMY_DATABASE_URI = database_uri


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

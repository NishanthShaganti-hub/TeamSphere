import os
from datetime import timedelta
from dotenv import load_dotenv

# Base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file if present
load_dotenv(os.path.join(basedir, ".env"))


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
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        f"sqlite:///{os.path.join(basedir, 'instance', 'teamsphere.db')}"
    )


class TestingConfig(Config):
    """Testing configuration isolated from development database."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = "test-secret-key-never-used-in-production"
    # Ensure secure cookie is disabled during local test runs
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration with strict security requirements."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    @classmethod
    def validate(cls):
        """Ensure critical secrets are configured in production."""
        secret = os.environ.get("SECRET_KEY")
        if not secret or "dev-insecure" in secret:
            raise ValueError("SECRET_KEY must be set to a secure, random value in production!")
        if not os.environ.get("DATABASE_URL"):
            raise ValueError("DATABASE_URL must be set in production!")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

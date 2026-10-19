"""
Application extensions initialized without application instances.
They will be bound to the application inside the create_app factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Database ORM
db = SQLAlchemy()

# User session authentication
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
login_manager.session_protection = "strong"

# Cross-Site Request Forgery (CSRF) protection
csrf = CSRFProtect()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
)

# Database schema migrations
migrate = Migrate()


# SQLite Foreign Keys Enforcement
# By default, SQLite disables foreign key constraints for backwards compatibility.
# This listener executes 'PRAGMA foreign_keys = ON' whenever an SQLite connection is opened.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints on all SQLite connections."""
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()
